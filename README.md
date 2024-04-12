# CDR Hook for NCSA pipeline

This repository contains the hook to receive messages from the CDR and starts the processing. The
processing has three (maye four) steps:
- download image to local disk
- if running on HPC check queue in rabbitmq and start sbatch a job
- run uiuc-pipeline to process the downloaded image
- upload the processed image back to CDR.

To use this application you need to first copy env.example to .env and modify the values. You will
at least need to set `SERVER_NAME` and `CDR_TOKEN`.

The unregister.sh script can be used to remove any hanging registrations with CDR, and the versions.sh
script can be used to set the version for the cdr-hook application.
