# Utility scripts

This folder contains utility scripts that are used on the HPC system to monitor queues and start models.

*upload_download.sh* - This script will download and start 2 apptainer containers (if not already started) and tail the output logs.
*model_launcher.sh* - This script will check if any models are needed to be run and start them. This will launch about 1 pipeline for every 10 waiting jobs.

Both scripts require a files called secrets.sh to be in the same folder. If it does not exist, it will print a message if it does not exist.
