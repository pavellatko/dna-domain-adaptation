#!/bin/bash
#SBATCH -n 1 -c 8 -G 4 --gpus-per-node 4 -t 1-12:00:00

module purge
module load Python/Anaconda_v05.2022

conda init bash
source ~/.bashrc

conda deactivate
conda activate adapt_env

LOGS_DIR="logs"
RUN_SCRIPT="train.run"

mkdir $LOGS_DIR

time cat $RUN_SCRIPT | parallel -j8 'export CUDA_VISIBLE_DEVICES=$((({%}-1)/2)); bash -c {}" >> '"$LOGS_DIR"'/train_{%}.log 2>&1"; bash -c {}" --phase test >> '"$LOGS_DIR"'/test_{%}.log 2>&1"'
