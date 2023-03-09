#!/bin/bash

mapfile -d '' DIR_ROOT <"$1"

DIR_DATA="$DIR_ROOT/data/"
DIR_RAW="$DIR_DATA/raw/"
DIR_GENOME="$DIR_DATA/genome/"
DIR_PREPROCESSED="$DIR_DATA/preprocessed/"

mkdir -p $DIR_PREPROCESSED

python3 \
    ./preprocess_bed.py \
    -i $DIR_RAW \
    -o $DIR_PREPROCESSED \
    -g $DIR_GENOME \
    -f
