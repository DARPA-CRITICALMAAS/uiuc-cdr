#!/bin/bash

if [ -n "$(apptainer instance list | grep criticalmaas-uploader)" ]; then
  echo "Stopping uplaoder"
  apptainer instance stop criticalmaas-uploader
fi 
rm -f criticalmaas-uploader.pid
if [ -n "$(apptainer instance list | grep criticalmaas-downloader)" ]; then
  echo "Stopping downloader"
  apptainer instance stop criticalmaas-downloader
fi
rm -f criticalmaas-downloader.pid
