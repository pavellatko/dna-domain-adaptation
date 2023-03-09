#!/bin/bash

mapfile -d '' DIR_ROOT <"$1"
mapfile -d '' ASSEMBLY_LIST <"$2"
mapfile -d '' ANTIGEN_CLASS <"$3"

DIR_DATA="$DIR_ROOT/data/"
DIR_RAW="$DIR_DATA/raw/"
DIR_CHIPATLAS="$DIR_DATA/chip-atlas/"

python3 \
    ./get_chip-atlas_bedfiles.py \
    --antigen-class $ANTIGEN_CLASS \
    --genome-assembly ${ASSEMBLY_LIST[*]} \
    --experimentlist "$DIR_CHIPATLAS/experimentList.tab" \
    --output-dir "$DIR_RAW"
