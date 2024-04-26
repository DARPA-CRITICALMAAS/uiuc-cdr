from flask import Flask, request, abort, current_app
from flask_httpauth import HTTPBasicAuth
import os
import logging
import json
import requests
import hmac
import hashlib
import urllib.parse
import pika
import signal
import sys
from waitress.server import create_server

auth = HTTPBasicAuth()
cdr_url = "https://api.cdr.land"


# ----------------------------------------------------------------------
# HELPER
# ----------------------------------------------------------------------
def strtobool (val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))


# ----------------------------------------------------------------------
# Authentication/Verification
# ----------------------------------------------------------------------
@auth.verify_password
def verify_password(username, password):
    """
    Check username/password. If no username/password is set as
    environment variables, default to anonymous.
    """
    u = current_app.config["callback_username"]
    p = current_app.config["callback_password"]
    if not u or not p:
        return "anonymous"
    if username == u and password == p:
        return username
    return None


# ----------------------------------------------------------------------
# Connection with RabbitMQ
# ----------------------------------------------------------------------
def send_message(message, queue):
    """
    Send a message to the RabbitMQ queue
    """
    parameters = pika.URLParameters(current_app.config["rabbitmq_uri"])
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    properties = pika.BasicProperties(delivery_mode=2)
    channel.basic_publish(exchange='', routing_key=queue, properties=properties, body=json.dumps(message))
    channel.close()
    connection.close()


# ----------------------------------------------------------------------
# Process incoming requests
# ----------------------------------------------------------------------
def process_map(cog_id, cog_url):
    """
    Process the map
    """
    logging.info("Processing COG %s from %s", cog_id, cog_url)
    message = {
        "cog_id": cog_id,
        "cog_url": cog_url,
        "system": current_app.config["name"],
        "version": current_app.config["version"]
    }
    headers = {'Authorization': f'Bearer {current_app.config["cdr_token"]}'}
    r = requests.get(f"{cdr_url}/v1/maps/cog/{cog_id}", headers=headers)
    r.raise_for_status()
    message['metadata'] = r.json()
    r = requests.get(f"{cdr_url}/v1/maps/cog/{cog_id}/results", headers=headers)
    r.raise_for_status()
    message['results'] = r.json()
    send_message(message, f'{current_app.config["prefix"]}download')


def validate_request(data, signature_header, secret):
    """
    Validate the incoming request. This is a simple check to see if the
    request is JSON.
    """
    logging.debug("Validating request with signature %s", signature_header)
    hash_object = hmac.new(secret.encode("utf-8"), msg=data, digestmod=hashlib.sha256)
    expected_signature = hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        abort(403, "Request signatures didn't match!")


@auth.login_required
def hook():
    """
    Our main entry point for CDR calls
    """
    # check the signature
    validate_request(request.data, request.headers.get("x-cdr-signature-256"), current_app.config["callback_secret"])

    data = request.get_json()
    logging.info("Received event : %s", data.get("event"))
    if data.get("event") == "ping":
        pass
    elif data.get("event") == "map.process":
        try:
            process_map(data["payload"]["cog_id"], data["payload"]["cog_url"])
        except Exception as e:
            logging.exception("Could not process hook")
            mesg = {
              "x-cdr-signature-256": request.headers.get("x-cdr-signature-256"),
              "exception": str(e),
              "data": request.data
            }
            send_message(mesg, f'{current_app.config["prefix"]}cdrhook.error')
    elif current_app.config["cdr_keep_event"]:
        send_message(data, f'{current_app.config["prefix"]}cdrhook.unknown')

    return {"ok": "success"}


# ----------------------------------------------------------------------
# Start the server and register with the CDR
# ----------------------------------------------------------------------
def register_system(config):
    """
    Register our system to the CDR using the app_settings
    """
    registration = {
        "name": config["name"],
        "version": config["version"],
        "callback_url": config["callback_url"],
        "webhook_secret": config["callback_secret"],
        "auth_header": config["callback_username"],
        "auth_token": config["callback_password"],
        # Registers for ALL events
        "events": []
    }
    headers = {'Authorization': f'Bearer {config["cdr_token"]}'}
    logging.info(
        f"Registering with CDR: [{registration['name']} {registration['version']} {registration['callback_url']}]")
    r = requests.post(f"{cdr_url}/user/me/register", json=registration, headers=headers)
    logging.debug(r.text)
    r.raise_for_status()
    logging.info("Registered with CDR, response: %s", r.json()["id"])
    return r.json()["id"]


def unregister_system(cdr_token, registration):
    """
    Unregister our system from the CDR
    """
    # unregister from the CDR
    headers = {'Authorization': f"Bearer {cdr_token}"}
    r = requests.delete(f"{cdr_url}/user/me/register/{registration}", headers=headers)
    logging.info("Unregistered with CDR")
    r.raise_for_status()


def create_app():
    """
    Create the Flask app, setting up the environment variables and
    register with CDR.
    """
    logging.info("Starting up")

    # set up the config variables
    app = Flask(__name__)
    app.config["name"] = os.getenv("SYSTEM_NAME")
    app.config["version"] = os.getenv("SYSTEM_VERSION")
    app.config["cdr_token"] = os.getenv("CDR_TOKEN")
    app.config["callback_url"] = os.getenv("CALLBACK_URL")
    app.config["callback_secret"] = os.getenv("CALLBACK_SECRET")
    app.config["callback_username"] = os.getenv("CALLBACK_USERNAME")
    app.config["callback_password"] = os.getenv("CALLBACK_PASSWORD")
    app.config["rabbitmq_uri"] = os.getenv("RABBITMQ_URI")
    app.config["prefix"] = os.getenv("PREFIX")
    app.config["cdr_keep_event"] = strtobool(os.getenv("CDR_KEEP_EVENT", "no"))

    # register with the CDR
    registration = register_system(app.config)
    app.config["registration"] = registration

    # register the hook
    path = urllib.parse.urlparse(app.config["callback_url"]).path
    logging.info("Registering hook at %s", path)
    app.route(path, methods=['POST'])(hook)

    # app has been created
    return app


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s [%(threadName)-15s] %(levelname)-7s :'
                               ' %(name)s - %(message)s',
                        level=logging.DEBUG)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARN)
    logging.getLogger('pika').setLevel(logging.WARN)

    app = create_app()
    server = create_server(app, host="0.0.0.0", port=8080)

    # signal handler, to do something before shutdown service
    # this does not work.
    def handle_sig(sig, frame):
        logging.warning(f"Got signal {sig}, now close worker...")
        unregister_system(app.config['cdr_token'], app.config['registration'])
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, signal.SIGHUP):
        signal.signal(sig, handle_sig)

    server.run()
    logging.info("Shutting down")
