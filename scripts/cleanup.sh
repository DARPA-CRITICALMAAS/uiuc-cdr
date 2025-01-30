#!/bin/bash

# Copyright (c) 2025 The Trustees of the University of Illinois
# licensed under the MIT License
# see "LICENSE" file in the distribution root directory

cd $(dirname $0)
./stop_apptainer.sh
rm -f ~/.apptainer/instances/logs/${HOSTNAME}/${USER}/criticalmaas-*
