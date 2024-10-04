# Utility scripts

This folder contains utility scripts that are used on the HPC system to monitor queues and start models.

*upload_download.sh* - This script will download and start 2 apptainer containers (if not already started) and tail the output logs.
*model_launcher.sh* - This script will check if any models are needed to be run and start them. This will launch about 1 pipeline for every 10 waiting jobs.

Both scripts require a files called secrets.sh to be in the same folder. If it does not exist, it will print a message that states the required variables needed in secrets.sh. An example of the contents of secrets.sh is,
```
# required variables
export CDR_TOKEN=this_is_a_secret_received_from_cdr
export RABBITMQ_URI=amqp://username:password@server.url:5672/%2F
export MONITOR_URL=https://server.url/monitor/queues.json
```
