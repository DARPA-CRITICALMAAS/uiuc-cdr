#!/bin/bash

# Copyright (c) 2025 The Trustees of the University of Illinois
# licensed under the MIT License
# see "LICENSE" file in the distribution root directory

if [ ! -e .env ]; then
  echo "Need .env for token."
  exit 1
fi
export TOKEN=$(awk -F '=' '/CDR_TOKEN/ { print $2 }' .env | sed 's/"//g')

IDS=$(curl -s -H "Authorization: Bearer ${TOKEN}" https://api.cdr.land/user/me/registrations | jq -r .[].id)
for ID in ${IDS}; do
  echo $ID
  curl -X DELETE -H "Authorization: Bearer ${TOKEN}" https://api.cdr.land/user/me/register/${ID}
done
