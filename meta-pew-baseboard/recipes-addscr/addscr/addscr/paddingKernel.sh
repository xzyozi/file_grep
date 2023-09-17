#!/bin/bash
#
# Copyright 2022 Panasonic Corporation
#

#Padding
LOADSIZE=($(cat CSFDescData.txt | grep Kernel_Load_Size))
objcopy -I binary -O binary --pad-to ${LOADSIZE[1]} --gap-fill=0x00 Image Image_pad.bin

#Make IVT
./genIVT.pl
cat Image_pad.bin ivt.bin > Image_pad_ivt.bin
