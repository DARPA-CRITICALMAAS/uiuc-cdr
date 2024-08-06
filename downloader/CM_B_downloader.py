import pika, sys, getopt, os
import json
import time
#import argparse

# configuration options; should come from environment variables or something
# this is the base of the working directory in the main (non-image) parallel
# file system

#my_data_dir="/projects/bbym/shared/CDR_processing/pipeline_processing_003"
try:
    my_local_dir=os.environ['CMAAS_LOCAL_DATA_DIR']
    my_data_dir=my_local_dir    
except KeyError:
    my_data_dir="/data"

print(f'Data dir is {my_data_dir}')

try:
    test_file_filename=os.environ['CMAAS_LOCAL_DIR_TEST_FILE']
    dir_test_file=os.path.join(my_data_dir,test_file_filename)
    open(dir_test_file,'a')
except KeyError:
    a='2'
    

print("")
print("CriticaMAAS B-stage downloader")

download_queue="download"

# name preamble for processing queues, to make it easier for humans to see the
# function of the processing queues
process_queue_base = "process_"

# current list of models.  Should come from an environment variable
#process_model_list = ["golden_muscat","flat_iceberg"]
process_model_list = ["golden_muscat","flat_iceberg","drab_volcano"]

# this is the actual running list of process queues that we will output
# requests to as we receive requests from CDR
#process_queue_list=[]

#rabbitmq_uri = "amqp://criticalmaas:keeNgoo1VahthuS4ii1r@rabbitmq.criticalmaas.software-dev.ncsa.illinois.edu:5672/shepard"
rabbitmq_uri = "amqp://ncsa:teef1Wor8iey9ohsheic@criticalmaas.ncsa.illinois.edu:5672/%2F"

###############
# this is only here because the include isn't working

RMQ_username = "criticalmaas"
RMQ_password = "keeNgoo1VahthuS4ii1r"

#
##############

def set_up_RMQ(secrets_file):
    global rabbitmq_uri
    #    global RMQ_username
#    global RMQ_password
    
#    if os.path.exists(secrets_file):
#        execfile(filename)
#    rabbitmq_uri = f"amqp://{RMQ_username}:{RMQ_password}@rabbitmq.criticalmaas.software-dev.ncsa.illinois.edu:5672/shepard"
    return rabbitmq_uri


def CDR_download_callback(ch, method, properties, body):
#    global my_log_dir
#    global my_input_dir
#    global my_output_dir
    global my_data_dir
    
    global rabbitmq_uri
    
    global process_model_list

    my_relative_filename=""
    
    print("***Received:")
    # catalog from CDR
    CDR_catalog=json.loads(body)
    print("got CDR catalog")
    #    print("map name:>>"+my_catalog['map_name']+"<<")

    print("about to print catalog")
    print(CDR_catalog)
    print("finished catalog")

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
        print("about to run maparea download command: "+DL_command)
        os.system(DL_command)
        print("finished maparea download command")

    if tif_file_URL:
        DL_command="cd "+my_data_dir+" ; mkdir -p "+external_data_path+" ; cd "+external_data_path+" ; wget "+tif_file_URL
        # check for file before downloading
        fetch_file_path=os.path.join(my_data_dir,external_data_path);
        fetch_file_components=tif_file_URL.split("/")
        fetch_file_total_path=os.path.join(fetch_file_path,fetch_file_components[-1])
        if os.path.isfile(fetch_file_total_path):
            print(f"File >{fetch_file_total_path}< already exists!  Skipping download.")
        else:
            print("about to run tif download command: "+DL_command)
            os.system(DL_command)
            print("finished tif download command")

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
        print("About to send process message:")
        print(outgoing_message)
        print("finished process message")
        parameters = pika.URLParameters(rabbitmq_uri)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=my_process_queue, durable=True)
        properties = pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
        channel.basic_publish(exchange='', routing_key=my_process_queue, body=outgoing_message, properties=properties)

    # exit after a single message processing for testing
#    sys.exit(2)
    print("pausing")
    time.sleep(2)

        
        
    #    result_file=input_dir+my_catalog['map_id']+".cog.tif"
    #    print("input dir:"+input_dir)
    #    print("resulting file: "+result_file)
    
        


def main(argv):
    my_input_file=""
    my_input_dir=""
    my_output_dir=""
    my_model_name=""

    global my_log_dir
    global my_pipeline_image
    global download_queue

    global process_queue_list
    global process_model_list
    global process_queue_base
    
#    queue=queue_base+"_"+my_model_name

    print("input file:>"+my_input_file+"<")
    print("output directory:>"+my_output_dir+"<")
    #print("using queue:>"+queue+"<")

#    for each model_name in process_model_list:
#        process_queue_list.append(process_queue_base+model_name)

#    print("total processing queue list:")
#    print(process_queue_list)
#    print("finished printing processing queue list.")
    
    # set up consumer
    rabbitmq_uri=set_up_RMQ("~/.criticalmaas/secrets")

    parameters = pika.URLParameters(rabbitmq_uri)
    print('About to open rabbitMQ connection')
    connection = pika.BlockingConnection(parameters)
    print('RabbitMQ connection succeeded!')
    channel = connection.channel()
    channel.queue_declare(queue=download_queue, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=download_queue, on_message_callback=CDR_download_callback, auto_ack=False)    
    # presumably this funtion takes us into a wait-process loop forever
    print('start consumer loop')
    channel.start_consuming()

    #    my_catalog=json.load(jfile)
                                         

    #    my_request_dictionary={'input': my_input , 'output': my_output}

    #    my_message = json.dumps(my_request_dictionary)

    #    print("extract from catalog: map_name="+my_catalog[0]["map_name"])

    # shouldn't get here, but just in case
    sys.exit(2)
    
    my_outgoing_message_dictionary={'map_name': my_catalog[catalog_line]['map_name'] , 'map_id': my_catalog[catalog_line]['map_id'], 'cog_url': my_catalog[catalog_line]['cog_url']}

    
    if len(my_input_file) > 0:
        print("creating a single-file dictionary")
        my_message_dictionary={'request_type': "input_file" , 'input_file': my_input_file , 'input_dir': my_input_dir, 'output_dir': my_output_dir, 'model': my_model_name, 'pipeline_image': my_pipeline_image, 'log_dir': my_log_dir}
    else:
        print("creating a directory (multi-file) dictionary")
        my_message_dictionary={'request_type': "input_dir" , 'input_dir': my_input_dir , 'output_dir': my_output_dir, 'model': my_model_name, 'pipeline_image': my_pipeline_image, 'log_dir': my_log_dir}
        
    my_message = json.dumps(my_message_dictionary)
    
    parameters = pika.URLParameters(rabbitmq_uri)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)

    properties = pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
##    message = "hello world"
    channel.basic_publish(exchange='', routing_key=queue, body=my_message, properties=properties)

# here's the thing we're feeding (from 2024 April 10th):
# apptainer run --nv -B ./logs:/logs  -B /projects/bbym/saxton/MockValData/:/data -B ./output:/output /projects/bbym/shared/continerExchange/criticalmaas-pipeline_latest.sif -v --log /logs/logs.latest --data /data/theFile.tif --legends /data/theFile.json
# added: --model flat_iceberg    
#
# apptainer run --nv -B ./logs:/logs  -B /projects/bbym/saxton/MockValData/:/data -B ./output:/output /projects/bbym



    print("finished producer main()")


if __name__ == '__main__':
    main(sys.argv[1:])
    
