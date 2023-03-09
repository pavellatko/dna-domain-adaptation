#!/bin/bash

mapfile -d '' DIR_ROOT <"$1"
mapfile -d '' DIR_MODELS <"$2"

DIR_DATA="$DIR_ROOT/data/"
DIR_PREPROCESSED="$DIR_DATA/preprocessed/"

python3 \
    ./generate_training_scripts.py \
    -i $DIR_PREPROCESSED \
    -m $DIR_MODELS \
    -p $DIR_MODELS/model_parameters.csv \
    -o $DIR_PREPROCESSED
