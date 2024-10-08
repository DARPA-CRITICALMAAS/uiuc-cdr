import pika, sys, getopt, os
import json
import time
#import argparse
import threading
from requests.exceptions import RequestException
import logging

# configuration options; should come from environment variables or something
# this is the base of the working directory in the main (non-image) parallel
# file system

#my_data_dir="/projects/bbym/shared/CDR_processing/pipeline_processing_003"
try:
    my_local_dir=os.environ['CMAAS_LOCAL_DATA_DIR']
    my_data_dir=my_local_dir    
except KeyError:
    my_data_dir="/data"

#print(f'Data dir is {my_data_dir}')

#logging.debug("Data dir is:")
#logging.debug(my_data_dir)

try:
    test_file_filename=os.environ['CMAAS_LOCAL_DIR_TEST_FILE']
    dir_test_file=os.path.join(my_data_dir,test_file_filename)
    open(dir_test_file,'a')
except KeyError:
    a='2'
    

#print("")
#print("CriticaMAAS B-stage downloader")

download_main_queue="download"
download_error_queue="download.error"

# name preamble for processing queues, to make it easier for humans to see the
# function of the processing queues
process_queue_base = "process_"

# current list of models.  Should come from an environment variable
#process_model_list = ["golden_muscat","flat_iceberg"]
process_model_list = ["golden_muscat","flat_iceberg","drab_volcano"]

# this is the actual running list of process queues that we will output
# requests to as we receive requests from CDR
#process_queue_list=[]

# RABBITMQ_URI *must* be defined in the incoming environment otherwise all the rabbitmq features will not work.  
rabbitmq_uri = os.getenv("RABBITMQ_URI", "amqp://guest:guest@localhost:5672/%2F")

# the downloader worker class
class DL_worker(threading.Thread):
    output_model_list = []
    output_message_dictionary = {}

    def process(self, method, properties, body_in):
        self.method = method
        self.properties = properties
        self.body_in = body_in
        self.exception = None

    def run(self):
        self.output_model_list.clear()
        try:
            CDR_catalog = json.loads(self.body_in)
            logging.debug("about to print catalog")
            logging.debug(CDR_catalog)
            logging.debug("finished catalog")

            # I don't think I need to, or even can, do this.  I don't think
            # I have the right kind of handle
            #            ch.basic_ack(delivery_tag=method.delivery_tag)
            

            # grabbing relevant portions of the incoming message.  
            tif_file_URL=CDR_catalog['cog_url']
            maparea_file_URL=CDR_catalog['map_data']
            CDR_model_list=CDR_catalog['models']
            my_cog_id=CDR_catalog['cog_id']
            logging.info(f"Processing COG {my_cog_id}")
            
            # figure out filenames and paths for everything

            # we split the target into intermediate directories to avoid pileup of tons
            # of entities in a single directory; this is for scaling to a parallel
            # filesystem with many man requests.  
            split_path=os.path.join(my_cog_id[0:2],my_cog_id[2:4])
            relative_file_location=os.path.join(split_path,my_cog_id)
            # this is where the data directory is mounted inside the image
            data_location_base=""
#            image_base_dir_absolute="/"+data_location_relative
            
            # the total path in the image where the data is reference from
            external_data_path=os.path.join(data_location_base,relative_file_location)
            tif_data_file_name=my_cog_id+".cog.tif"
            #    maparea_data_file_name=my_cog_id+".cog_area.json"
            maparea_data_file_name=my_cog_id+".map_data.json"

            # here we have the actual paths for the files we're going to (potentially) download
            tif_filename_with_path=os.path.join(relative_file_location,tif_data_file_name)
            maparea_filename_with_path=os.path.join(relative_file_location,maparea_data_file_name)
            
            # if the incoming message specified a maparea file, get it
            if maparea_file_URL:
                # rm -f is because there's no clean way to tell wget to overwrite files; so this guarantees that the file is the newest downloaded one.  
                DL_command="cd "+my_data_dir+" ; mkdir -p "+external_data_path+" ; cd "+external_data_path+" ; rm -f "+maparea_data_file_name+" ; wget -q "+maparea_file_URL
                logging.debug("about to run maparea download command: "+DL_command)
                os.system(DL_command)
                #time.sleep(2)
                logging.debug("finished maparea download command")
                
            # if the incoming message specified an image file, get it
            if tif_file_URL:
                DL_command="cd "+my_data_dir+" ; mkdir -p "+external_data_path+" ; cd "+external_data_path+" ; wget -q "+tif_file_URL
                # check for file before downloading
                fetch_file_path=os.path.join(my_data_dir,external_data_path);
                fetch_file_components=tif_file_URL.split("/")
                fetch_file_total_path=os.path.join(fetch_file_path,fetch_file_components[-1])
                if os.path.isfile(fetch_file_total_path):
                    logging.debug(f"File >{fetch_file_total_path}< already exists!  Skipping download.")
                else:
                    logging.debug("about to run tif download command: "+DL_command)
                    os.system(DL_command)
                    #time.sleep(5)
                    logging.debug("finished tif download command")
                    
            # construct and send processing orders based on the incoming message, and
            # what we downloaded.  For completeness, we also include the entire incoming
            # catalog for easier tracking
            outgoing_message_dictionary=CDR_catalog;
            outgoing_message_dictionary["image_filename"]=tif_filename_with_path
            outgoing_message_dictionary["json_filename"]=maparea_filename_with_path
            self.output_message_dictionary=outgoing_message_dictionary
            for model_to_process in CDR_model_list:
                self.output_model_list.append(model_to_process)
            
#        except RequestException as e:
#            logging.exception(f"Request Error {response.text}.")
#            self.exception = e
        except Exception as e:
            logging.exception("Error processing download .")
            self.exception = e


            
def CDR_download_callback(ch, method, properties, body):
#    global my_log_dir
#    global my_input_dir
#    global my_output_dir
    global my_data_dir
    
    global rabbitmq_uri
    
    global process_model_list

    my_relative_filename=""
    
    logging.debug("***Received:")
    # catalog from CDR
    CDR_catalog=json.loads(body)
    logging.debug("got CDR catalog")
    #    print("map name:>>"+my_catalog['map_name']+"<<")

    logging.debug("about to print catalog")
    logging.debug(CDR_catalog)
    logging.debug("finished catalog")

    # ack here so the request gets removed from the stack before
    # downloading; downloading can be minutes
    ch.basic_ack(delivery_tag=method.delivery_tag)
    # (FYI: putting the ack here doesn't help the timeout.  We will still be suseptible
    # to the heartbeat timeout if the download time exceeds 60 seconds
    
    # download the file first
    # (perhaps to be replaced by more python-y alternative from Rob)
    tif_file_URL=CDR_catalog['cog_url']
    maparea_file_URL=CDR_catalog['map_data']
    CDR_model_list=CDR_catalog['models']
    my_cog_id=CDR_catalog['cog_id']

    # we split the target into intermediate directories to avoid pileup of tons
    # of entities in a single directory; this is for scaling to a parallel
    # filesystem with many man requests.  
    split_path=os.path.join(my_cog_id[0:2],my_cog_id[2:4])
    extended_split_path=os.path.join(split_path,my_cog_id)
    # this is where the data directory is mounted inside the image
    external_data_base_dir_relative="data"
    image_data_base_dir_absolute="/"+external_data_base_dir_relative

    # the total path in the image where the data is reference from
    #    image_data_path=os.path.join(image_data_base_dir_absolute,extended_split_path)
    external_data_path=os.path.join(external_data_base_dir_relative,extended_split_path)
    tif_data_file_name=my_cog_id+".cog.tif"
#    maparea_data_file_name=my_cog_id+".cog_area.json"
    maparea_data_file_name=my_cog_id+".map_data.json"
    
    # this is the location of the data file within the container, relative to its canonical folder (probably "/data")
    #    tif_filename_with_path=os.path.join(image_data_path,tif_data_file_name)
    tif_filename_with_path=os.path.join(extended_split_path,tif_data_file_name)
    maparea_filename_with_path=os.path.join(extended_split_path,maparea_data_file_name)
    
    #    external_data_filename_with_path=os.path.join(external_data_path,tif_data_file_name)

    if maparea_file_URL:
        # rm -f is because there's no clean way to tell wget to overwrite files; so this guarantees that the file is the newest downloaded one.  
        DL_command="cd "+my_data_dir+" ; mkdir -p "+external_data_path+" ; cd "+external_data_path+" ; rm -f "+maparea_data_file_name+" ; wget "+maparea_file_URL
        logging.debug("about to run maparea download command: "+DL_command)
        os.system(DL_command)
        logging.debug("finished maparea download command")

    if tif_file_URL:
        DL_command="cd "+my_data_dir+" ; mkdir -p "+external_data_path+" ; cd "+external_data_path+" ; wget "+tif_file_URL
        # check for file before downloading
        fetch_file_path=os.path.join(my_data_dir,external_data_path);
        fetch_file_components=tif_file_URL.split("/")
        fetch_file_total_path=os.path.join(fetch_file_path,fetch_file_components[-1])
        if os.path.isfile(fetch_file_total_path):
            logging.debug(f"File >{fetch_file_total_path}< already exists!  Skipping download.")
        else:
            logging.debug("about to run tif download command: "+DL_command)
            os.system(DL_command)
            logging.debug("finished tif download command")

    # set up message; the message is only specific to the request file, not to
    # the model, so we can set up a message to be sent to all of the processing
    # queues.  

    # construct outgoing request catalog from incoming CDR catalog
    #        outgoing_message_dictionary={'request_type': "input_file" , 'input_file': CDR_catalog['cog_url'] , 'input_dir': my_input_dir, 'output_dir': my_output_dir, 'model': model_to_process, 'pipeline_image': my_pipeline_image, 'log_dir': my_log_dir}
    #        outgoing_message_dictionary={'request_type': "input_file" , 'input_file': CDR_catalog['cog_url'] , 'input_dir': my_input_dir, 'output_dir': my_output_dir, 'model': model_to_process, 'log_dir': my_log_dir, 'cog_id': CDR_catalog['cog_id'], 'metadata': CDR_catalog['metadata'], 'results': CDR_catalog['results'] }

    # Pass whole catalog on, with additions to make the inference pipeline work
    outgoing_message_dictionary=CDR_catalog;
    outgoing_message_dictionary["image_filename"]=tif_filename_with_path
    outgoing_message_dictionary["json_filename"]=maparea_filename_with_path
    
    # then send out processing requests
    #    for model_to_process in process_model_list:
    for model_to_process in CDR_model_list:
        my_process_queue = process_queue_base+model_to_process

        outgoing_message=json.dumps(outgoing_message_dictionary)
        logging.debug("About to send process message:")
        logging.debug(outgoing_message)
        logging.debug("finished process message")
        parameters = pika.URLParameters(rabbitmq_uri)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=my_process_queue, durable=True)
        properties = pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
        channel.basic_publish(exchange='', routing_key=my_process_queue, body=outgoing_message, properties=properties)

    # exit after a single message processing for testing
#    sys.exit(2)
#    print("pausing")
#    time.sleep(2)

        
        
    #    result_file=input_dir+my_catalog['map_id']+".cog.tif"
    #    print("input dir:"+input_dir)
    #    print("resulting file: "+result_file)
    
        


def main(argv):
    my_input_file=""
    my_input_dir=""
    my_output_dir=""
    my_model_name=""

    global rabbitmq_uri
    global my_log_dir
    global my_pipeline_image
    global download_queue

    global process_queue_list
    global process_model_list
    global process_queue_base
    
    #    queue=queue_base+"_"+my_model_name

    logging.debug(f'Data directory is {my_data_dir}')


#    print("input file:>"+my_input_file+"<")
#    print("output directory:>"+my_output_dir+"<")

    parameters = pika.URLParameters(rabbitmq_uri)
    logging.debug('About to open rabbitMQ connection')
    connection = pika.BlockingConnection(parameters)
    logging.info('RabbitMQ connection succeeded!')
    channel = connection.channel()

    # from this point, following the template from the uploader
    channel.queue_declare(queue=download_main_queue, durable=True)
    channel.queue_declare(queue=download_error_queue, durable=True)
    # We only know for sure our incoming download queue and its error queue.  
    # Queues for models are defined according to incoming messages, so we
    # don't pre-declare them here.  
    
    # Defining prefetch count here to be 1 means that if we're processing something but
    # we haven't closed it out, and we asked for another, we get an empty response.  
    channel.basic_qos(prefetch_count=1)
    
    # here's where the flow bifurcase from my oringinal non-threaded downloader

    # consumer iterator to pull messages off the download queue
    consumer = channel.consume(queue=download_main_queue, inactivity_timeout=1)

    worker = None
    while True:
        # grab the next message from the download queue
        # We only get a real message when there is a message waiting and we've
        # closed out the last one
        logging.debug("loop")
        method, properties, body = next(consumer)
        if method:
            # if there was a new message with real information in it,
            # we fire off a worker with its contents
            worker = DL_worker()
            worker.process(method, properties, body)
            worker.start()

        if worker:
            if not worker.is_alive():
                # if the worker has finished its task, we grab its contents, send out
                # its messages, and then close it out to the queue iterator
                my_model_list = worker.output_model_list
                my_output_dictionary = worker.output_message_dictionary

                if worker.exception:
                    my_output_dictionary['exception'] = repr(worker.exception)
                    channel.basic_publish(exchange='', routing_key=download_error_queue,
                                          body=json.dumps(my_output_dictionary),
                                          properties=worker.properties)
                else:
                    # send a process message for each model in the list
                    for model_to_process in my_model_list:
                        logging.debug(f"sending process request for model {model_to_process}")
                        my_process_queue = process_queue_base+model_to_process
                        outgoing_message=json.dumps(my_output_dictionary)
                        channel.queue_declare(queue=my_process_queue, durable=True)
                        channel.basic_publish(exchange='', routing_key=my_process_queue, body=outgoing_message, properties=worker.properties)
                channel.basic_ack(delivery_tag=worker.method.delivery_tag)
                worker = None
                
            
    print ("should never get here!  Exiting!")
    sys.exit(2)
                    



if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s [%(threadName)-15s] %(levelname)-7s :'
                        ' %(name)s - %(message)s',
                        level=logging.getLevelName(os.getenv("LOGLEVEL", "INFO").upper()))
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARN)
    logging.getLogger('pika').setLevel(logging.WARN)
    main(sys.argv[1:])
    
