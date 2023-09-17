#!/bin/bash
#
# Copyright 2022 Panasonic Corporation
#

LOADADDR=($(cat CSFDescData.txt | grep Kernel_Load_Addr))
LOADSIZE=($(cat CSFDescData.txt | grep Kernel_Load_Size))
PADSIZE=($(cat CSFDescData.txt | grep Kernel_Pad_Size))
SELFPOINT=$(printf '0x%x' $((LOADADDR[1]+LOADSIZE[1])))
CSFPOINT=$(printf '0x%x' $((LOADADDR[1]+PADSIZE[1])))

sed -e "s|0x.*); # Load Address|${LOADADDR[1]}); # Load Address|g" \
    -e "s|0x.*); # Self Pointer|$SELFPOINT); # Self Pointer|g" \
    -e "s|0x.*); # CSF Pointer|$CSFPOINT); # CSF Pointer|g" \
    -i genIVT.pl

