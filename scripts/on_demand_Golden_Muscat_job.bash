#!/bin/bash

#SBATCH -p a100
#SBATCH -A bbym-hydro
#SBATCH --time 08:00:00
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=craigsteffen@gmail.com
##SBATCH --cpus_per_task=56
#SBATCH -o CM_golden_muscat-%j.out
#SBATCH -e CM_golden_muscat-%j.err
INTERNAL_MODEL="golden_muscat"

cd "/projects/bbym/shared/CDR_processing/pipeline_processing_003"

# old URI
#       --amqp amqp://guest:guest@rabbitmqserver:5672/%2F \

CONTAINER_FILE="./criticalmaas-pipeline_latest.sif"

if [ ! -e ${CONTAINER_FILE} ]; then
    echo "container file ${CONTAINER_FILE} does not exist!  Exiting."
    exit
    #  apptainer pull criticalmaas-pipeline.sif docker://ncsa/criticalmaas-pipeline:rabbitmq
fi

mkdir -p data output validation legends layouts logs feedback

#export CDR_SYSTEM="UIUC"
#export CDR_SYSTEM_VERSION="0.4.1"

JOBS=""
GPUS=$(nvidia-smi --list-gpus | wc -l)
echo "gpu list: ${GPUS}"
echo $GPUS
echo 	  "GPU list finished"

#for GPU_NUM in $(seq 0 $(( $GPUS - 1 )) ); do
    #    --layout /layouts \
    #    --validation /validation \
#    echo "setting up GPU # ${GPU_NUM}"
#export CUDA_VISIBLE_DEVICES=${GPU_NUM}
apptainer run --nv \
      -B ./data:/data \
      -B ./output:/output \
	      -B ./legends:/legends \
	      -B ./layouts:/layouts \
	      -B ./feedback:/feedback \
	      -B ./logs:/logs \
	      -B /projects/bbym/shared/models/:/checkpoints \
	      ${CONTAINER_FILE} \
	      -v \
	      --inactive_timeout 60 \
	      --data /data \
	      --output /output \
	      --legends /legends \
	      --layout /layouts \
	      --feedback /feedback \
	      --checkpoint_dir /checkpoints \
	      --output_types cdr_json raster_masks \
	      --log /logs/gpu-${SLURM_JOBID}.log \
	      --amqp amqp://ncsa:teef1Wor8iey9ohsheic@criticalmaas.ncsa.illinois.edu:5672/%2F \
	      --model ${INTERNAL_MODEL} &> log.${SLURM_JOBID}_${HOSTNAME}.txt &
#	      --model golden_muscat &> log.${SLURM_JOBID}_${HOSTNAME}_${GPU_NUM}.txt &
#	      --gpu ${GPU_NUM} \
#	      --log /logs/gpu-${SLURM_JOBID}_${GPU_NUM}.log \
#	      --output_types cdr_json geopackage raster_masks \

#
#	      --idle 60 \
JOB_ID="$!"
JOBS="${JOBS} ${JOB_ID}"
#    echo "Started ${JOB_ID} on GPU ${GPU_NUM}"
echo "Started ${JOB_ID}"
#done

for JOB in ${JOBS}; do
  echo "Waiting for $JOB"
  wait $JOB
done
