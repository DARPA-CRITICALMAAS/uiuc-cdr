from flask import Flask, request, abort, current_app, send_from_directory
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
import threading
import time

auth = HTTPBasicAuth()
cdr_url = "https://api.cdr.land"

config = { }

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
    u = config["callback_username"]
    p = config["callback_password"]
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
    parameters = pika.URLParameters(config["rabbitmq_uri"])
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    properties = pika.BasicProperties(delivery_mode=2)
    channel.basic_publish(exchange='', routing_key=queue, properties=properties, body=json.dumps(message))
    channel.close()
    connection.close()

# ----------------------------------------------------------------------
# Process maps
# ----------------------------------------------------------------------
def check_uncharted_event(event_id):
    """
    If the event is an unchared event, we will download the data, and fire
    the download event.
    """
    # get the event information
    headers = {'Authorization': f'Bearer {config["cdr_token"]}'}
    r = requests.get(f"{cdr_url}/v1/maps/extractions/{event_id}", headers=headers)
    r.raise_for_status()
    data = r.json()

    # parse the infomation
    cog_id = None
    map_area = None
    polygon_legend_area = None
    line_point_legend_area = None
    cog_area = None
    for extraction in data:
        cog_id = extraction["cog_id"]
        for area in extraction["cog_area_extractions"]:
            if area["category"] == "map_area":
                map_area = area
            elif area["category"] == "polygon_legend_area":
                polygon_legend_area = area
            elif area["category"] == "line_point_legend_area":
                line_point_legend_area = area
        if map_area:
            cog_area = extraction
    if not cog_id or not map_area:
        logging.error("Could not find cog_id or map_area in uncharted event")
        return

    # write the cog_area to disk
    folder = os.path.join(cog_id[0:2], cog_id[2:4])
    filepart = os.path.join(folder, cog_id)
    filename = os.path.join("/data", f"{filepart}.cog_area.json")
    os.makedirs(os.path.dirname(filename) , exist_ok=True)
    with open(filename, "w") as outputfile:
        json.dump(cog_area, outputfile)

    # get the basic information
    r = requests.get(f"{cdr_url}/v1/maps/cog/{cog_id}", headers=headers)
    r.raise_for_status()
    cog_info = r.json()

    # send the download event
    firemodels = [ ] 
    for k, v in config["models"].items():
        goodmodel = True
        if "map_area" in v and not map_area:
            logging.debug("Skipping %s because of map_area", k)
            goodmodel = False
        if "polygon_legend_area" in v and not polygon_legend_area:
            logging.debug("Skipping %s because of polygon_legend_area", k)
            goodmodel = False
        if "line_point_legend_area" in v and not line_point_legend_area:
            logging.debug("Skipping %s because of line_point_legend_area", k)
            goodmodel = False
        if goodmodel:
            firemodels.append(k)

    message = {
        "cog_id": cog_id,
        "cog_url": cog_info["cog_url"],
        "map_area": f'{config["callback_url"]}/download/{filepart}.cog_area.json',
        "models": firemodels
    }
    logging.info("Firing download event for %s '%s'", cog_id, json.dumps(message))
    send_message(message, f'{config["prefix"]}download')


# ----------------------------------------------------------------------
# Process incoming requests
# ----------------------------------------------------------------------
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
    if request.headers.get("x-cdr-signature-256"):
       validate_request(request.data, request.headers.get("x-cdr-signature-256"), config["callback_secret"])
    elif not request.headers.get("x-ncsa-secret", "") == config["callback_secret"]:
        abort(403, "Callback secret didn't match!")

    send_message(request.get_json(), f'{config["prefix"]}cdrhook')
    return {"ok": "success"}


@auth.login_required
def download(filename):
    """
    download the file
    """
    logging.info(f"Received download request for {filename}")
    return send_from_directory("/data", filename)

# ----------------------------------------------------------------------
# Start the server and register with the CDR
# ----------------------------------------------------------------------
def cdrhook_callback(channel, method, properties, body):
    """
    Callback to process maps without required metadata. This will check
    a map every 30 seconds to see if the metadata is available. If not
    it will be added to the back of the queue.
    """
    try:
        data = json.loads(body)

        if not data.get("event"):
            logging.error("No event in message")
        elif data.get("event") == "ping":
            logging.debug("ping/pong")
        elif data.get("event") == "map.process":
            logging.debug("ignoring map.process")
        elif data.get("event") == "feature.process":
            event_id = data.get("payload", {}).get("id", "").strip()
            if event_id.startswith("uncharted-area_0."):
                check_uncharted_event(event_id)
            else:
                logging.debug(f"Ignoring feature.process with id {event_id}")
        else:
            logging.debug("Unknown event %s", data.get("event"))
        
        if config["cdr_keep_event"]:
            send_message(data, f'{config["prefix"]}cdrhook.unknown')
    except Exception as e:
        logging.exception("Error processing cdrhook message.")
        data["exception"] = repr(e)
        send_message(data, f'{config["prefix"]}cdrhook.error')
    channel.basic_ack(delivery_tag=method.delivery_tag)

def cdrhook_listener(config):
    """
    Listen to the RabbitMQ queue and process the messages. The messages
    are maps that need to be processed, but don't have the required
    metadata yet.
    """
    logging.info("Starting RabbitMQ listener")

    while True:
        try:
            # connect to rabbitmq
            parameters = pika.URLParameters(config['rabbitmq_uri'])
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # create all queues needed
            channel.queue_declare(queue=f'{config["prefix"]}cdrhook', durable=True)
            channel.queue_declare(queue=f'{config["prefix"]}cdrhook.error', durable=True)

            # process messages
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=f'{config["prefix"]}cdrhook', on_message_callback=cdrhook_callback, auto_ack=False)
            channel.start_consuming()
        except Exception as e:
            logging.exception("Error running cdrhook.")
        time.sleep(5)

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
        "callback_url": f'{config["callback_url"]}/hook',
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
    config["name"] = os.getenv("SYSTEM_NAME")
    config["version"] = os.getenv("SYSTEM_VERSION")
    config["cdr_token"] = os.getenv("CDR_TOKEN")
    config["callback_url"] = os.getenv("CALLBACK_URL")
    config["callback_secret"] = os.getenv("CALLBACK_SECRET")
    config["callback_username"] = os.getenv("CALLBACK_USERNAME")
    config["callback_password"] = os.getenv("CALLBACK_PASSWORD")
    config["rabbitmq_uri"] = os.getenv("RABBITMQ_URI")
    config["prefix"] = os.getenv("PREFIX")
    config["cdr_keep_event"] = strtobool(os.getenv("CDR_KEEP_EVENT", "no"))
    
    # load the models
    with open("models.json", "r") as f:
        config["models"] = json.load(f)

    # register with the CDR
    registration = register_system(config)
    config["registration"] = registration

    # register the hook
    path = urllib.parse.urlparse(config["callback_url"]).path
    app.route(os.path.join(path, "hook"), methods=['POST'])(hook)
    app.route(os.path.join(path, "download", "<path:filename>"), methods=['GET'])(download)

    # start daemon thread for rabbitmq
    thread = threading.Thread(target=cdrhook_listener, args=(config,))
    thread.daemon = True
    thread.start()

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
        unregister_system(config['cdr_token'], config['registration'])
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, signal.SIGHUP):
        signal.signal(sig, handle_sig)

    server.run()
    logging.info("Shutting down")
