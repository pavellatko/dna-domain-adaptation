#!/bin/bash

mapfile -d '' DIR_ROOT <"$1"

DIR_DATA="$DIR_ROOT/data/"
DIR_GENOME="$DIR_DATA/genome/"
DIR_GAP="$DIR_DATA/gap/"
DIR_PREPROCESSED="$DIR_DATA/preprocessed/"

python3 \
    ./generate_random_samples.py \
    -i $DIR_PREPROCESSED \
    -g $DIR_GENOME \
    --dir-gap $DIR_GAP \
    -f
