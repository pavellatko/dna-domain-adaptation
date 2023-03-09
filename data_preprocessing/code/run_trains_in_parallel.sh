#!/bin/bash

# must be absolute
DIR_CODE="/home/fpavlov/projects/2022-08-tl/code"
DIR_PREPROCESSED="/home/fpavlov/projects/2022-08-tl/data/preprocessed"

for i in $(ls $DIR_PREPROCESSED); do
    cd $DIR_PREPROCESSED/$i ; $DIR_CODE/run_parallel.sh
done