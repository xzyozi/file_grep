#!/bin/bash
#
# Copyright 2022 Panasonic Corporation
#

SPLOFF=($(cat CSFDescData.txt | grep SPL_Auth_Off))
FITOFF=($(cat CSFDescData.txt | grep FIT_Auth_Off))

echo "#!/bin/bash" > addSignature.sh
echo >> addSignature.sh
echo "cp ../../../work/${MACHINE}-poky-linux/imx-boot/1.0-r0/git/iMX8M/flash.bin ./signed_imx-boot.bin" >> addSignature.sh

echo >> addSignature.sh
echo "#Add signature to SPL" >> addSignature.sh
echo "dd if=csf_spl.bin of=signed_imx-boot.bin seek=\$((${SPLOFF[1]})) bs=1 conv=notrunc" >> addSignature.sh

echo >> addSignature.sh
echo "#Add signature to FIT" >>addSignature.sh
echo "dd if=csf_fit.bin of=signed_imx-boot.bin seek=\$((${FITOFF[1]})) bs=1 conv=notrunc" >> addSignature.sh

echo >> addSignature.sh
echo "#Add signature to Kernel" >> addSignature.sh
echo "cat Image_pad_ivt.bin csf_Image.bin > Image_signed.bin" >> addSignature.sh
chmod +x addSignature.sh
