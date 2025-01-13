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

# CDR VERSION
if [ -z "${CDR}" ]; then
    CDR=$(curl -s https://api.github.com/repos/DARPA-CRITICALMAAS/uiuc-cdr/releases/latest | jq -r .tag_name | sed 's/^v//')
fi

# print versions
echo "CDR      : $CDR"

# download images if they don't exist
if [ ! -e criticalmaas-cleanup_${CDR}.sif ]; then
    apptainer pull --force criticalmaas-cleanup_${CDR}.sif docker://ncsa/criticalmaas-cleanup:${CDR}
    rm -f criticalmaas-cleanup_latest.sif
    ln -s criticalmaas-cleanup_${CDR}.sif criticalmaas-cleanup_latest.sif
fi

# start images if not running
if [ -z "$(apptainer instance list | grep criticalmaas-cleanup)" ]; then
    apptainer instance run \
        --pid-file criticalmaas-cleanup.pid \
        --no-home \
        --contain \
        --bind ./data:/data \
        --bind ./output:/output \
        --env "RABBITMQ_URI=${RABBITMQ_URI}" \
        criticalmaas-cleanup_latest.sif \
        criticalmaas-cleanup \
            python /src/cleanup.py

# showing log files
echo "----------------------------------------------------------------------"
echo "Showing log files, press Ctr-C to exit"
echo "tail -f ~/.apptainer/instances/logs/${HOSTNAME}/${USER}/criticalmaas-*"
echo "----------------------------------------------------------------------"
tail -f ~/.apptainer/instances/logs/${HOSTNAME}/${USER}/criticalmaas-*
