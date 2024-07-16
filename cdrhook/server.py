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
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import cdrhook.retrieve as retrieve
import cdrhook.convert as convert
from cdrhook.connector import CdrConnector
# from cmaas_utils.io import saveCMASSMap
from cmaas_utils.types import CMAAS_Map
from cdr_schemas.cdr_responses.area_extractions import AreaType


auth = HTTPBasicAuth()
cdr_url = "https://api.cdr.land"

config = { }
cdr_connector = None

# ----------------------------------------------------------------------
# region HELPER
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
# region Authentication/Verification
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
# region Connection with RabbitMQ
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
# region Process maps
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

def process_cog(cdr_connector : CdrConnector , cog_id : str, config_parm : Optional[dict]=None):
    """
    Processing callback for cogs. Checks if there is enough information available
    to process the cog with the requested models. If there is downloads the 
    prereq data from the CDR, saves it to a temporary file and fires the download
    event to rabbitmq.

    cdr_connector : CdrConnector, CDR Connection with a registered connection
    cog_id : str, The cog_id to process
    config_parm : dict, Optional field to overwrite the global config parameters, needed for unit testing

    """
    if config_parm is None:
        config_parm = config
    valid_area_systems = ['uncharted']
    valid_legend_systems = ['polymer', 'uncharted']

    logging.info(f"{cog_id[0:8]} - Processing cog {cog_id}")
    # Retrieve available system versions for this cog and check if there are any valid systems posted
    sys_ver_response = retrieve.retrieve_cog_system_versions(cdr_connector, cog_id)
    cog_system_versions = retrieve.validate_cog_system_versions_response(sys_ver_response)
    valid_systems = False
    for system in cog_system_versions.system_versions:
        if system.name in valid_area_systems or system.name in valid_legend_systems:
            valid_systems = True
            break

    if not valid_systems:
        # logging.error(f"{cog_id[0:8]} - No valid system data found on CDR")
        raise ValueError(f"No valid system data found on CDR for {cog_id}")
        # return
    else:
        logging.info(f"{cog_id[0:8]} - Available system versions : {cog_system_versions.pretty_str()}")

    # Retrieve cdr data for this cog
    with ThreadPoolExecutor() as p:
        area_future = p.submit(retrieve.retrieve_cog_area_extraction, cdr_connector, cog_id)
        legend_future = p.submit(retrieve.retrieve_cog_legend_items, cdr_connector, cog_id)
        
        area_response = area_future.result()
        legend_response = legend_future.result()

    # Validate responses to cdr_schema objects
    cog_area_extraction = retrieve.validate_cog_area_extraction_response(area_response)
    cog_legend_items = retrieve.validate_cog_legend_items_response(legend_response)

    # Filter out systems that are not valid
    cog_area_extraction = [ae for ae in cog_area_extraction if ae.system in valid_area_systems]
    cog_legend_items = [li for li in cog_legend_items if li.system in valid_legend_systems]

    # Check there is enough data to process
    ae_categories = {AreaType.Map_Area: 0, AreaType.Polygon_Legend_Area: 0, AreaType.Line_Point_Legend_Area: 0}
    for ae in cog_area_extraction:
        if ae.category not in ae_categories:
            ae_categories[ae.category] = 1
        else:
            ae_categories[ae.category] += 1
    logging.info(f"{cog_id[0:8]} - Found {ae_categories}")
    poly_map_units = [mu for mu in cog_legend_items if mu.category == 'polygon']
    logging.info(f"{cog_id[0:8]} - Found {len(poly_map_units)} polygon map units")
    
    valid_map_area, valid_polygon_legend_area, valid_polygon_map_units = True, True, True
    if ae_categories[AreaType.Map_Area] < 1:
        logging.error(f"{cog_id[0:8]} - No map area found")
        valid_map_area = False
        # return
    if ae_categories[AreaType.Line_Point_Legend_Area] < 1:
        logging.error(f"{cog_id[0:8]} - No line point legend area found")
        valid_line_point_legend_area = False
        # return
    if ae_categories[AreaType.Polygon_Legend_Area] < 1:
        logging.error(f"{cog_id[0:8]} - No polygon legend area found")
        valid_polygon_legend_area = False
        # return
    if len(poly_map_units) < 1:
        logging.error(f"{cog_id[0:8]} - No polygon legend items found")
        valid_polygon_map_units = False
        # return
    
    firemodels = [ ] 
    for model, prereqs in config_parm["models"].items():
        goodmodel = True
        if "map_area" in prereqs and not valid_map_area:
            logging.debug("Skipping %s because of map_area", model)
            goodmodel = False
        if "polygon_legend_area" in prereqs and not valid_polygon_legend_area:
            logging.debug("Skipping %s because of polygon_legend_area", model)
            goodmodel = False
        if "line_point_legend_area" in prereqs and not valid_line_point_legend_area:
            logging.debug("Skipping %s because of line_point_legend_area", model)
            goodmodel = False
        if "polygon_map_units" in prereqs and not valid_polygon_map_units:
            logging.debug("Skipping %s because of polygon_map_units", model)
            goodmodel = False
        logging.info(f"{cog_id[0:8]} - Firing download event for {model}")
        if goodmodel:
            firemodels.append(model)

    if len(firemodels) == 0:
        raise ValueError(f"No valid models found for {cog_id}")
        
    # Retrieve download link for the geotiff
    cog_download_response = retrieve.retrieve_cog_download(cdr_connector, cog_id)
    cog_download = retrieve.validate_cog_download_response(cog_download_response)

    # Convert cdr obects to cmass objects for saving
    layout = convert.convert_cdr_schema_area_extraction_to_layout(cog_area_extraction)
    legend = convert.convert_cdr_schema_legend_items_to_cmass_legend(cog_legend_items)
    map_data = CMAAS_Map(name=cog_id, cog_id=cog_id, layout=layout, legend=legend)

    # write the cog_area to disk
    folder = os.path.join(cog_id[0:2], cog_id[2:4])
    filepart = os.path.join(folder, cog_id)
    filename = os.path.join("/data", f"{filepart}.map_data.json")
    if 'mode' in config_parm and config_parm['mode'] == 'test': # Can't write to /data in tests
        filename = os.path.join('tests', 'data', f'{filepart}.map_data.json')
    os.makedirs(os.path.dirname(filename) , exist_ok=True)

    with open(filename, "w") as fh:
        fh.write(map_data.model_dump_json())
    # saveCMASSMap(filename, map_data)

    message = {
        "cog_id": cog_id,
        "cog_url": cog_download.cog_url,
        "map_data": f'{cdr_connector.callback_url}/download/{filepart}.map_data.json',
        "models": firemodels
    }
    logging.info("Firing download event for %s '%s'", cog_id, json.dumps(message))
    if 'mode' in config_parm and config_parm['mode'] != 'test': # Can't send rabbitmq in tests
        send_message(message, f'{config_parm["prefix"]}download')

# ----------------------------------------------------------------------
# region Process incoming requests
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
def cog(id):
    """
    Process the cog
    """
    logging.info(f"Received process cog for {id}")
    send_message({"event": "ncsacog", "cog_id": id}, f'{config["prefix"]}cdrhook')

    return {"ok": "success"}


@auth.login_required
def download(filename):
    """
    download the file
    """
    logging.info(f"Received download request for {filename}")
    return send_from_directory("/data", filename)

# ----------------------------------------------------------------------
# region Start the server and register with the CDR
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
        elif data.get("event") == "ncsacog":
            cog_id = data.get("cog_id", "").strip()
            process_cog(cog_id)
        elif data.get("event") == "map.process":
            logging.debug("ignoring map.process")
        elif data.get("event") == "feature.process":
            event_id = data.get("payload", {}).get("id", "").strip()
            if event_id.startswith("uncharted_0."):
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

def create_app():
    """
    Create the Flask app, setting up the environment variables and
    register with CDR.
    """
    logging.info("Starting up")

    # set up the config variables
    app = Flask(__name__)
    # config["name"] = os.getenv("SYSTEM_NAME")
    # config["version"] = os.getenv("SYSTEM_VERSION")
    # config["cdr_token"] = os.getenv("CDR_TOKEN")
    # config["callback_url"] = os.getenv("CALLBACK_URL")
    # config["callback_secret"] = os.getenv("CALLBACK_SECRET")
    # config["callback_username"] = os.getenv("CALLBACK_USERNAME")
    # config["callback_password"] = os.getenv("CALLBACK_PASSWORD")
    config["rabbitmq_uri"] = os.getenv("RABBITMQ_URI")
    config["prefix"] = os.getenv("PREFIX")
    config["cdr_keep_event"] = strtobool(os.getenv("CDR_KEEP_EVENT", "no"))
    
    # load the models
    with open("models.json", "r") as f:
        config["models"] = json.load(f)

    # register with the CDR
    cdr_connector = CdrConnector(
        system_name=os.getenv("SYSTEM_NAME"),
        system_version=os.getenv("SYSTEM_VERSION"),
        token=os.getenv("CDR_TOKEN"),
        callback_url=os.getenv("CALLBACK_URL")+'/hook',
        callback_secret=os.getenv("CALLBACK_SECRET"),
        callback_username=os.getenv("CALLBACK_USERNAME"),
        callback_password=os.getenv("CALLBACK_PASSWORD"),
    )
    cdr_connector.register()
    config["cdr_connector"] = cdr_connector

    # register the hook
    path = urllib.parse.urlparse(config["callback_url"]).path
    app.route(os.path.join(path, "hook"), methods=['POST'])(hook)
    app.route(os.path.join(path, "download", "<path:filename>"), methods=['GET'])(download)
    app.route(os.path.join(path, "cog", "<string:id>"), methods=['POST'])(cog)

    # start daemon thread for rabbitmq
    thread = threading.Thread(target=cdrhook_listener, args=(config,))
    thread.daemon = True
    thread.start()

    # app has been created
    return app


# ----------------------------------------------------------------------
# region main
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
        cdr_connector.unregister()
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGQUIT, signal.SIGHUP):
        signal.signal(sig, handle_sig)

    server.run()
    logging.info("Shutting down")
