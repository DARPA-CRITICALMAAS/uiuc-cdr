#!/bin/bash

# check requirements
if [ ! -e /usr/bin/docker ]; then
    echo "Docker is not installed, please install docker"
    exit 1
fi
if [ ! -e /usr/bin/jq ]; then
    echo "jq is not installed, please install jq"
    exit 1
fi

# fetch latest versions
CDR_TAG=$(curl -s https://api.github.com/repos/DARPA-CRITICALMAAS/uiuc-cdr/releases/latest | jq -r '.tag_name')
PIPELINE_TAG=$(curl -s https://api.github.com/repos/DARPA-CRITICALMAAS/uiuc-pipeline/releases/latest | jq -r '.tag_name')

# -------------------------------------------------------
# load secrets.sh file, if not exist create template
# -------------------------------------------------------
if [ ! -e "./secrets.sh" ]; then
    cat << "EOF" > secrets.sh
# -------------------------------------------------------
# what profile to use by default
# -------------------------------------------------------
export PROFILE=allinone
# -------------------------------------------------------
# common variables
# -------------------------------------------------------
export SERVER_NAME="$(hostname -f)"
export CDR_TOKEN=this_is_a_secret_received_from_cdr
export CDR_URL=https://api.cdr.land
export RABBITMQ_USERNAME=guest
export RABBITMQ_PASSWORD=guest
# only change this if you have an external rabbitmq server
export RABBITMQ_MGMT_URL=http://rabbitmq:15672
# -------------------------------------------------------
# for cdrhook docker-compose
# -------------------------------------------------------
# letsencrypt email address
export EMAIL_ADDRESS="cert@${SERVER_NAME}"
export CDRHOOK_URL=https://${SERVER_NAME}/cdr
export CDRHOOK_SECRET=you-should-change-this
export CDRHOOK_VERSION=latest
# -------------------------------------------------------
# for pipeline docker-compose/launcher
# -------------------------------------------------------
export RABBITMQ_URI=amqp://${RABBITMQ_USERNAME}:${RABBITMQ_PASSWORD}@${SERVER_NAME}:5672/%2F
export MONITOR_URL=https://{SERVER_NAME}/monitor/queues.json
# using a specific version of the pipeline
export PIPELINE_VERSION=latest
EOF
    echo "Please update the secrets.sh file with the correct values"
    exit 1
fi
source ./secrets.sh

# print message about version being used
if [ "${CDRHOOK_VERSION}" != "" -a "${CDRHOOK_VERSION}" != "latest" ]; then
    echo "Using NCSA cdrhook version      : ${CDRHOOK_VERSION}"
    if [ "${CDRHOOK_VERSION}" != "${CDR_TAG}" ]; then
    echo "Latest NCSA cdrhook version is  : ${CDR_TAG}"
    fi
else
    echo "Using NCSA cdrhook version      : ${CDR_TAG} (latest)"
    export CDRHOOK_VERSION=${CDR_TAG}
fi
if [ "${PIPELINE_VERSION}" != "" -a "${PIPELINE_VERSION}" != "latest" ]; then
    echo "Using NCSA pipeline version     : ${PIPELINE_VERSION}"
    if [ "${PIPELINE_VERSION}" != "${PIPELINE_TAG}" ]; then
    echo "Latest NCSA pipeline version is : ${PIPELINE_TAG}"
    fi
else
    echo "Using NCSA pipeline version     : ${PIPELINE_TAG} (latest)"
    export PIPELINE_VERSION=${PIPELINE_TAG}
fi

echo "${CALLBACK_URL}"
# remove the v from the docker version
export CDRHOOK_VERSION=$(echo ${CDRHOOK_VERSION} | sed 's/v//')
export PIPELINE_VERSION=$(echo ${PIPELINE_VERSION} | sed 's/v//')

# -------------------------------------------------------
# download latest released docker-compose file
# -------------------------------------------------------
if [[ -n "${CDR_BRANCH}" ]]; then
    URL="https://raw.githubusercontent.com/DARPA-CRITICALMAAS/uiuc-cdr/refs/heads/${CDR_BRANCH}/"
else
    URL="https://raw.githubusercontent.com/DARPA-CRITICALMAAS/uiuc-cdr/refs/tags/${CDR_TAG}/"
fi
curl -L -s $URL/docker-compose.yml -o docker-compose.yml

# -------------------------------------------------------
# create .env file
# -------------------------------------------------------
cat << EOF > .env
SERVER_NAME="${SERVER_NAME}"
CDR_URL="${CDR_URL}"

TRAEFIK_ACME_EMAIL="${EMAIL_ADDRESS}"

CDR_TOKEN="${CDR_TOKEN}"
CDRHOOK_VERSION="${CDRHOOK_VERSION}"

CALLBACK_PATH=/hook
CALLBACK_URL="${CDRHOOK_URL}"
CALLBACK_SECRET="${CDRHOOK_SECRET}"
CALLBACK_USERNAME=""
CALLBACK_PASSWORD=""

RABBITMQ_USERNAME="${RABBITMQ_USERNAME}"
RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD}"
RABBITMQ_MGMT_URL="${RABBITMQ_MGMT_URL}"

PIPELINE_VERSION="${PIPELINE_VERSION}"
EOF

# -------------------------------------------------------
# create docker-compose.override file
# -------------------------------------------------------
if [ -e docker-compose.override.yml ]; then
    echo "docker-compose.override.yml already exists, skipping"
else
    cat << "EOF" > docker-compose.override.yml
services:
  # ----------------------------------------------------------------------
  # Add SSL to traefik
  # ----------------------------------------------------------------------
#   traefik:
#     command:
#       - --log.level=INFO
#       - --api=true
#       - --api.dashboard=true
#       - --api.insecure=true
#       # Entrypoints
#       - --entrypoints.http.address=:80
#       - --entrypoints.http.http.redirections.entryPoint.to=https
#       - --entrypoints.https.address=:443
#       - --entrypoints.https.http.tls.certresolver=myresolver
#       # letsencrypt
#       - --certificatesresolvers.myresolver.acme.email=${TRAEFIK_ACME_EMAIL}
#       - --certificatesresolvers.myresolver.acme.storage=/config/acme.json
#       # uncomment to use testing certs
#       #- --certificatesresolvers.myresolver.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory
#       - --certificatesresolvers.myresolver.acme.httpchallenge=true
#       - --certificatesresolvers.myresolver.acme.httpchallenge.entrypoint=http
#       # Docker setup
#       - --providers.docker=true
#       - --providers.docker.endpoint=unix:///var/run/docker.sock
#       - --providers.docker.exposedbydefault=false
#       - --providers.docker.watch=true
#     ports:
#       - "80:80"
#       - "443:443"

  # default models for cdrhook
  cdrhook:
    volumes:
      - ./models.json:/app/models.json
      - ./systems.json:/app/systems.json

  # open up rabbitmq
  rabbitmq:
    labels:
      - "traefik.enable=true"
      - "traefik.http.services.rabbitmq.loadbalancer.server.port=15672"
      - "traefik.http.routers.rabbitmq.rule=Host(`${SERVER_NAME}`)"

  # Add dependency of rabbitmq
  icy-resin:
    depends_on:
      - rabbitmq

  downloader:
    depends_on:
      - rabbitmq

  uploader:
    depends_on:
      - rabbitmq

# -------------------------------------------------------
# mount volumes to local file system
# -------------------------------------------------------
volumes:
# following probably don't need to be mounted to local
# file system (i.e large NFS storage), this should only
# use minimal space.
#  traefik
#  rabbitmq:
# following probably should be mounted to larger file
# system (i.e. NFS storage).
# hold json objects to process in cdrhook
#   cdrhook:
#     driver: local
#     driver_opts:
#       type: none
#       device: /data/volumes/cdrhook
#       o: bind
# hold output from pipeline
#   feedback:
#     driver: local
#     driver_opts:
#       type: none
#       device: /data/volumes/feedback
#       o: bind
#   data:
#     driver: local
#     driver_opts:
#       type: none
#       device: /data/volumes/data
#       o: bind
#   logs:
#     driver: local
#     driver_opts:
#       type: none
#       device: /data/volumes/logs
#       o: bind
#   output:
#     driver: local
#     driver_opts:
#       type: none
#       device: /data/volumes/output
#       o: bind
EOF
fi

# -------------------------------------------------------
# create rabbitmq configuraion file
# -------------------------------------------------------
if [ -e 50-criticalmaas.conf ]; then
    echo "50-criticalmaas.conf already exists, skipping"
else
    cat << "EOF" > 50-criticalmaas.conf
consumer_timeout = 7200000
EOF
fi

# -------------------------------------------------------
# create default models and systems file
# -------------------------------------------------------
if [ -e models.json ]; then
    echo "models.json already exists, skipping"
else
    cat << "EOF" > models.json
{
    "icy_resin": ["map_area", "polygon_legend_area"]
}
EOF
fi
if [ -e systems.json ]; then
    echo "systems.json already exists, skipping"
else
    cat << "EOF" > systems.json
{
    "area": ["uncharted-area"],
    "legend": ["polymer"]
}
EOF
fi

# -------------------------------------------------------
# start the full stack
# -------------------------------------------------------
echo ""
docker compose --profile ${PROFILE} up -d
echo ""

# -------------------------------------------------------
# finished
# -------------------------------------------------------
echo "Quickstart complete"
echo "Please visit http://${SERVER_NAME}/monitor/ to access the RabbitMQ monitor interface"
echo "Please visit http://${SERVER_NAME} to access the RabbitMQ management interface"
