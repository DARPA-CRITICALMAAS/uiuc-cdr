#!/bin/bash

if [ ! -e secrets.sh ]; then
    cat <<EOF
Missing secrets.sh file. Please create one with the following variables:

# required variables
export CDR_TOKEN=this_is_a_secret_received_from_cdr
export RABBITMQ_URI=amqp://username:password@server.url:5672/%2F
export MONITOR_URL=https://server.url/monitor/queues.json
# using a specific version of the pipeline
export PIPELINE=pr36
EOF
    exit 0
fi
source secrets.sh

# PIPELINE VERSION
if [ -z "${PIPELINE}" ]; then
    PIPELINE=$(curl -s https://api.github.com/repos/DARPA-CRITICALMAAS/uiuc-pipeline/releases/latest | jq -r .tag_name | sed 's/^v//')
fi

# CDR VERSION
if [ -z "${CDR}" ]; then
    CDR=$(curl -s https://api.github.com/repos/DARPA-CRITICALMAAS/uiuc-cdr/releases/latest | jq -r .tag_name | sed 's/^v//')
fi

# print versions
echo "PIPELINE : $PIPELINE"
echo "CDR      : $CDR"

# download images if they don't exist
if [ ! -e criticalmaas-downloader_${CDR}.sif ]; then
    apptainer pull --force criticalmaas-downloader_${CDR}.sif docker://ncsa/criticalmaas-downloader:${CDR}
    rm -f criticalmaas-downloader_latest.sif
    ln -s criticalmaas-downloader_${CDR}.sif criticalmaas-downloader_latest.sif
fi
if [ ! -e criticalmaas-uploader_${CDR}.sif ]; then
    apptainer pull --force criticalmaas-uploader_${CDR}.sif docker://ncsa/criticalmaas-uploader:${CDR}
    rm -f criticalmaas-uploader_latest.sif
    ln -s criticalmaas-uploader_${CDR}.sif criticalmaas-uploader_latest.sif
fi
if [ ! -e criticalmaas-pipeline_${PIPELINE}.sif ]; then
    apptainer pull --force criticalmaas-pipeline_${PIPELINE}.sif docker://ncsa/criticalmaas-pipeline:${PIPELINE}
    rm -f criticalmaas-pipeline_latest.sif
    ln -s criticalmaas-pipeline_${PIPELINE}.sif criticalmaas-pipeline_latest.sif
fi

# make folders
mkdir -p data output logs/downloader logs

# start images if not running
if [ -z "$(apptainer instance list | grep criticalmaas-downloader)" ]; then
    apptainer instance run \
        --pid-file criticalmaas-downloader.pid \
        --no-home \
        --contain \
        --bind ./data:/data \
        --env "RABBITMQ_URI=${RABBITMQ_URI}" \
        criticalmaas-downloader_latest.sif \
        criticalmaas-downloader \
            python /src/CM_B_downloader.py
fi
if [ -z "$(apptainer instance list | grep criticalmaas-uploader)" ]; then
    apptainer instance run \
        --pid-file criticalmaas-uploader.pid \
        --no-home \
        --contain \
        --bind ./output:/output \
        --env "RABBITMQ_URI=${RABBITMQ_URI}" \
        --env "CDR_TOKEN=${CDR_TOKEN}" \
        criticalmaas-uploader_latest.sif \
        criticalmaas-uploader \
            python /src/uploader.py
fi

# showing log files
echo "----------------------------------------------------------------------"
echo "Showing log files, press Ctr-C to exit"
echo "tail -f ~/.apptainer/instances/logs/${HOSTNAME}/${USER}/criticalmaas-*"
echo "----------------------------------------------------------------------"
tail -f ~/.apptainer/instances/logs/${HOSTNAME}/${USER}/criticalmaas-*
