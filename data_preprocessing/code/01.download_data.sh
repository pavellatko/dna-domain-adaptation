#!/bin/bash

mapfile -d '' DIR_ROOT <"$1"
mapfile -d '' ASSEMBLY_LIST <"$2"

# DIR_ROOT=$1
DIR_DATA="$DIR_ROOT/data"
DIR_RAW="$DIR_DATA/raw"
DIR_GENOME="$DIR_DATA/genome"
DIR_GAP="$DIR_DATA/gap"
DIR_CHIPATLAS="$DIR_DATA/chip-atlas/"

mkdir -p $DIR_DATA $DIR_GAP $DIR_GENOME $DIR_RAW $DIR_CHIPATLAS

echo "Root directory: $DIR_ROOT"
echo "Assemblies: ${ASSEMBLY_LIST[*]}"

# mm9 and dm3 gaps are missing from UCSC
echo "Downloading gaps..."
for ASSEMBLY in ${ASSEMBLY_LIST[*]}; do
    wget -c -q --show-progress -O $DIR_GAP/$ASSEMBLY.gap.txt.gz http://hgdownload.cse.ucsc.edu/goldenpath/$ASSEMBLY/database/gap.txt.gz
    if ! test -f $DIR_GAP/$ASSEMBLY.gap.txt; then
        cd $DIR_GAP && gzip -ckd $ASSEMBLY.gap.txt.gz | cut -f2,3,4 >$ASSEMBLY.gap.txt
    fi
done

echo "Downloading chrom.sizes..."
for ASSEMBLY in ${ASSEMBLY_LIST[*]}; do
    wget -c -q --show-progress -P $DIR_GENOME https://hgdownload.cse.ucsc.edu/goldenpath/$ASSEMBLY/bigZips/$ASSEMBLY.chrom.sizes
done

echo "Downloading genome files..."
for ASSEMBLY in ${ASSEMBLY_LIST[*]}; do
    wget -c -q --show-progress -P $DIR_GENOME http://hgdownload.cse.ucsc.edu/goldenpath/$ASSEMBLY/bigZips/$ASSEMBLY.fa.gz
    if ! test -f $DIR_GENOME/$ASSEMBLY.fa; then
        cd $DIR_GENOME && gzip -kd $ASSEMBLY.fa.gz
    fi
done

echo "Downloading ChIP-Atlas data..."
wget -c -q --show-progress -P $DIR_CHIPATLAS https://dbarchive.biosciencedbc.jp/kyushu-u/metadata/fileList.tab
wget -c -q --show-progress -P $DIR_CHIPATLAS https://dbarchive.biosciencedbc.jp/kyushu-u/metadata/experimentList.tab

# for ASSEMBLY in ${ASSEMBLY_LIST[*]}; do
#     if grep -q "dm6" <<<$ASSEMBLY; then
#         wget -c -q --show-progress -P $DIR_CHIPATLAS https://dbarchive.biosciencedbc.jp/kyushu-u/$ASSEMBLY/allPeaks_light/allPeaks_light.$ASSEMBLY.05.bed.gz
#     fi
# done
