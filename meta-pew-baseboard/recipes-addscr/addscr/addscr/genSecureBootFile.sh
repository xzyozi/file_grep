#!/bin/bash
#
# Copyright 2022 Panasonic Corporation
#

./getCSFDescriptionData.sh
if [ $? -ne 0 ]; then
    exit 1
fi

./updateScr_genIVT.sh
if [ $? -ne 0 ]; then
    exit 1
fi

./paddingKernel.sh
if [ $? -ne 0 ]; then
    exit 1
fi

./makeScr_addSignature.sh
if [ $? -ne 0 ]; then
    exit 1
fi

./getCSFbin.sh
if [ $? -ne 0 ]; then
    exit 1
fi

./addSignature.sh
if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "Secure boot files have been generated."
