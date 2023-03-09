#!/bin/bash
# https://stackoverflow.com/questions/43686878/pass-multiple-arrays-as-arguments-to-a-bash-script

DIR_ROOT="/home/fpavlov/projects/2022-08-tl/"
DIR_MODELS="$DIR_ROOT/models"

ASSEMBLY_LIST=("ce11" "dm6" "hg38" "mm10" "sacCer3")
ANTIGEN_CLASS="Histone"
# ANTIGEN_CLASS="TFs"

# ./01.download_data.sh \
#     <(((${#DIR_ROOT})) && printf '%s\0' "${DIR_ROOT}") \
#     <(((${#ASSEMBLY_LIST[@]})) && printf '%s\0' "${ASSEMBLY_LIST[@]}") &&
    ./02.get_chip-atlas_bedfiles.sh \
        <(((${#DIR_ROOT})) && printf '%s\0' "${DIR_ROOT}") \
        <(((${#ASSEMBLY_LIST[@]})) && printf '%s\0' "${ASSEMBLY_LIST[@]}") \
        <(((${#ANTIGEN_CLASS})) && printf '%s\0' "${ANTIGEN_CLASS}")
    # ./03.preprocess_bed.sh \
    #     <(((${#DIR_ROOT})) && printf '%s\0' "${DIR_ROOT}") \
    #     <(((${#ASSEMBLY_LIST[@]})) && printf '%s\0' "${ASSEMBLY_LIST[@]}") &&
    # ./04.generate_random_samples.sh \
    #     <(((${#DIR_ROOT})) && printf '%s\0' "${DIR_ROOT}") &&
    # ./05.generate_training_scripts.sh \
    #     <(((${#DIR_ROOT})) && printf '%s\0' "${DIR_ROOT}") \
    #     <(((${#DIR_MODELS})) && printf '%s\0' "${DIR_MODELS}")
