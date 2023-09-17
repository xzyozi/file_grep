#!/bin/bash
#
# Copyright 2022 Panasonic Corporation
#

./getCSFDescriptionData.sh
RET=$?
if [ $RET -ne 0 ]; then
    exit 1
fi

./updateScr_genIVT.sh
RET=$?
if [ $RET -ne 0 ]; then
    exit 1
fi

./paddingKernel.sh
RET=$?
if [ $RET -ne 0 ]; then
    exit 1
fi

./makeScr_addSignature.sh
RET=$?
if [ $RET -ne 0 ]; then
    exit 1
fi

echo "Next, update CSF with CST tool."
echo "You can use the value of CSFDescData.txt"
