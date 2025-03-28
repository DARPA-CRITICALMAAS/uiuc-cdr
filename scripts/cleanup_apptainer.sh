#!/bin/bash

cd $(dirname $0)
./stop_apptainer.sh
rm -f ~/.apptainer/instances/logs/${HOSTNAME}/${USER}/criticalmaas-*
