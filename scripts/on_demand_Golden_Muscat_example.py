import pika,sys,getopt
import os
import json
import subprocess
import time


#input_queue = "download"
#input_queue = "process_flat_iceberg"
input_queue = "process_golden_muscat"
#input_queue = "upload"
#output_queue = "send_to_processing"
#input_queue = "test_upload"
primary_batch_script="/projects/bbym/shared/CDR_processing/pipeline_processing_003/golden_muscat_launcher.bash"
#secondary_batch_scripts=["/projects/bbym/shared/CDR_processing/pipeline_processing_003/drab_volcano_launcher.bash"]

global input_dir
input_dir=""
global output_dir
output_dir=""

###############
# this is only here because the include isn't working

RMQ_username = "criticalmaas"
RMQ_password = "keeNgoo1VahthuS4ii1r"

#
##############

def how_many_messages_in_queue(secrets_file,queue_name):
    rabbitmq_uri=set_up_RMQ(secrets_file)

    parameters = pika.URLParameters(rabbitmq_uri)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    my_queue=channel.queue_declare(queue=queue_name,durable=True)
    return_val=my_queue.method.message_count
    connection.close()
    return my_queue.method.message_count




"""
def launch_job_return_ID_special(batch_file):
    global secondary_batch_scripts
    # run for launching when it's the *first* job launched in a while
    # This function also fires off a couple of secondary jobs that are
    # expected to run for a short time but then will terminate, leaving
    # the main ones running for this program to keep track of.
    for aux_batch_file in secondary_batch_scripts:
        print("running secondary script")
        subprocess.run(['sbatch', aux_batch_file], stdout=subprocess.PIPE)
    return launch_job_return_ID(batch_file)
"""
def launch_job_return_ID(batch_file):
    sbatch_result=subprocess.run(['sbatch', batch_file], stdout=subprocess.PIPE)
    sbatch_string=sbatch_result.stdout.decode('utf-8')    
    sbatch_output_list=sbatch_string.split()
    # (hopefully) returns the jobid of the new job
    return sbatch_output_list[3]

def how_many_of_my_jobs_running(job_list):
    job_total=0
    for check_job in job_list:
        squeue_result=subprocess.run(['squeue'], stdout=subprocess.PIPE)
        squeue_string=squeue_result.stdout.decode('utf-8')
        sq_line_list=squeue_string.splitlines()
        is_job_running=0
        for myline in sq_line_list:
            segment_list = myline.split()
            #            print(f"first segment:{segment_list[0]}")
            current_job = segment_list[0]
            if check_job == current_job:
                job_total += 1
                is_job_running=1
                #print(f"  ****match!: {check_job} {current_job}")
                #else:
                #print(f"no match: {check_job} {current_job}")
        # if the job isn't in the job list, then it's not running, so we can
        # remove it from the job list
        if is_job_running == 0:
            job_list.remove(check_job)
            print(f"removing job {check_job} from the job list")
    return job_total

def set_up_RMQ(secrets_file):
    global RMQ_username
    global RMQ_password
    
    if os.path.exists(secrets_file):
        execfile(filename)

    #    rabbitmq_uri = f"amqp://{RMQ_username}:{RMQ_password}@rabbitmq.criticalmaas.software-dev.ncsa.illinois.edu:5672/shepard"
    rabbitmq_uri = "amqp://ncsa:teef1Wor8iey9ohsheic@criticalmaas.ncsa.illinois.edu:5672/%2F"
    return rabbitmq_uri

"""
def callback(ch, method, properties, body):
    print("***Received:")
    my_catalog=json.loads(body)
    print("got catalog")
    print(my_catalog)
    #    print("map name:>>"+my_catalog['map_name']+"<<")
    """

"""
    file_URL=my_catalog['cog_url']
    DL_command="cd "+input_dir+" ; wget "+file_URL
    print("download command: "+DL_command)
"""

"""
    #    print("about to run download command")
    #    os.system(DL_command)
    #    print("finished download command")
    
#    result_file=input_dir+my_catalog['cog_id']+".cog.tif"
    print("input dir:"+input_dir)
#    print("resulting file: "+result_file)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print('about to sleep for 1 seconds')
    time.sleep(.2)
    print('finished ack')
#    sys.exit(2)
"""
    
def main(argv):
    # secrets file per-user
    global input_queue
    global primary_batch_script

    input_queue_count=how_many_messages_in_queue("~/.criticalmaas/secrets",input_queue)
    print(f"Queue has {input_queue_count} items.")

    job_list=[]
    #    job_ID=launch_job_return_ID(primary_batch_script)
    #print(f"launched job {job_ID}")
    #job_list.append(job_ID)

    #print("about to sleep")
    #time.sleep(2)

    #for i in range(180):
    #        my_job_count=how_many_of_my_jobs_running(job_list)
    #        print(f"There are {my_job_count} of our jobs running ({i}).")
    #        time.sleep(1)

    while True :
        target_job_count = 0
        process_count=how_many_messages_in_queue("~/.criticalmaas/secrets",input_queue)
        if process_count > 0:
            target_job_count += 1
        if process_count > 10:
            target_job_count += 1
        if process_count > 20:
            target_job_count += 1
        if process_count > 30:
            target_job_count += 2
        currently_running=how_many_of_my_jobs_running(job_list)
        print(f"Status (prelaunch): downloads to process={process_count}, current jobs running={currently_running}, target_jobs={target_job_count}")
        jobs_launched=0
        while currently_running < target_job_count :
            job_ID=launch_job_return_ID(primary_batch_script)
            print(f"Launching job {job_ID}")
            job_list.append(job_ID)
            currently_running=how_many_of_my_jobs_running(job_list)
            jobs_launched += 1
        print(f"Status (postlaunch): downloads to process={process_count}, current jobs running={currently_running}, target_jobs={target_job_count}")
        time.sleep(300)
#        time.sleep(15)
            

    print("exiting for debugging.")
    sys.exit(2)

    

    
    """
    rabbitmq_uri=set_up_RMQ("~/.criticalmaas/secrets")

    parameters = pika.URLParameters(rabbitmq_uri)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=input_queue, durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=input_queue, on_message_callback=callback, auto_ack=False)
    """
    print("Input data directory:"+input_dir)
    print("Output data directory:"+output_dir)
    print("Now beginning consuming loop:")

    """
    channel.start_consuming()
    """
    
if __name__ == '__main__':
    main(sys.argv[1:])
#    main()

