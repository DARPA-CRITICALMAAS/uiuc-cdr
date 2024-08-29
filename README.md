# CDR Hook for NCSA pipeline

This repository contains the hook to receive messages from the CDR and starts the processing. The full stack consists of a few containers that work together:

- **traefik** : This is the http proxy and can be ignored if you have another proxy already running (for example Route 53 in AWS). If not used disable it to prevent  it from binding to port 80/443. 
- **rabbitmq**: The orchestrator of all the work, all other containers connect to this and will receive work. If any of the messages can not be handled it will be added to the `<queue>.error` with the exception attached to the original message.
- **cdrhook**: this is the entry point for all work, it will register with the CDR and receive messages when new work needs to be done. When a message arrives it will check to see if all necessary metadata is available and if so, it will send a message to the `download` queue.
- **downloader**: this will download the image and the metadata to a shared folder that can be used by the actual processing container. This can run on a different server than the cdrhook, but does need to have access to the same storage system that the pipeline uses. Once it is downloaded it will send a message to each of the pipelines that run a model using the `process_<model>` queue name.
- **pipeline**: this will do the actual inference of the map, it will use the map and the metadata and find all the legends and appropriate regions in the map and write the result to the output folder ready for the CDR, and send a message to the `upload` queue.
- **uploader**: this will upload the processed data from the pipeline to the CDR and move the message to `completed` queue.
- **monitor**: this not really part of the system, but will show the number of messages in the different queues, making it easy to track overall progress.

## Running the pipeline

The whole system can be started using the [docker-compose.yml](docker-compose.yml) file and a configuration file called `.env`:

```yaml
# server name used both for rules and cdr callback
SERVER_NAME="fqdn.example.com"

# used for lets encrypt
TRAEFIK_ACME_EMAIL="yourname@example.com"

# name used to register and write to CDR
SYSTEM_NAME="UIUC"
SYSTEM_VERSION="v0.4.5"

# token to register and interact with CDR
CDR_TOKEN="please_check_with_CDR"

# call back information send to CDR
CALLBACK_PATH="/hook"
CALLBACK_SECRET="this_is_a_really_silly_secret"
CALLBACK_USERNAME=""
CALLBACK_PASSWORD=""

# configuration for rabbitmq
RABBITMQ_MGMT_URL="http://rabbitmq:15672"
RABBITMQ_USERNAME="guest"
RABBITMQ_PASSWORD="guest"
```

If you do not plan to expose the `rabbitmq` interface to the internet, and everything runs on the same server, you can use the default passwords listed above, however it is still recommended to pick something stronger.

The docker-compose file uses profiles to allow for different parts to be executed based on your environment:

- **default**: this will start `traefik`, `rabbitmq`, `cdrhook` and `monitor`
- **pipeline**: this will additionally start `downloaded`, `golden_muscat` and `uploader`.

To run additional models, you will need to copy the `golden_muscat` section in the docker-compose file and replace all references to golden_muscat to the other model (for example icy_resin). The model executions require a GPU, and we have tested this with a Nvidia A100 with 80GB.

For example to run the full system, you would execute `docker compose --profile pipeline up -d`, which will start the full stack and you will be able to see the monitor by going to the server url.

### Volumes

By default docker will create volumes that it manages to store all data. If you want to point it to specific locations you will need to create a `docker-compose.override.yml` file that specifies the storage locations, for example, to specify the output folder location, you use:

```yaml
volumes:
  output:
    driver: local
    driver_opts:
      type: none
      device: /data/volumes/output
      o: bind
```

An example can be found at [docker-compose.example.yml](docker-compose.example.yml) and can be renamed to be `docker-compose.override.yml`.

## HPC

When running on a HPC system, you will need to run the default profile on a server that is connected to the internet, and expose the rabbitmq server to the HPC cluster. On the HPC you will run the pieces from the pipeline. On the headnode you run the `downloader` and `uploader` and use scripts to check the number of jobs waiting in the queue, and launch jobs on the HPC to pick up the jobs from rabbitmq.

*In the near future we will have some helper scripts in the scripts folder*.

- download image to local disk
- if running on HPC check queue in rabbitmq and start sbatch a job
- run uiuc-pipeline to process the downloaded image
- upload the processed image back to CDR.

## TODO

- [ ] Move traefik to a profile so it needs to be started explicitly.
