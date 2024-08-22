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

# start monitoring process queues
while [ 1 == 1 ]; do
    LOG="$(date) :"
    SKIP="\n"
    for queue in golden_muscat icy_resin; do
        RUNNING=$(squeue --name=${queue} --user ${USER} --noheader | wc -l)
        JOBS=$(curl -s ${MONITOR_URL}?search=$queue | jq -r '.[0].total')
        NEEDED=$(( (JOBS + 9) / 10 ))
        NEEDED=$(( $NEEDED > 5 ? 5 : ${NEEDED} ))
        if [ $RUNNING -lt $NEEDED ]; then
            echo -en "${SKIP}Starting another pipeline for $queue. "
            SKIP=""
            sbatch --job-name ${queue} "/projects/bbym/shared/CDR_processing/pipeline_processing_003/${queue}_launcher.bash"
        fi
        LOG="${LOG} [$queue : Running=$RUNNING jobs=$JOBS need=$NEEDED]  "
    done
    echo -ne "${LOG}  \r"
    sleep 1
done
