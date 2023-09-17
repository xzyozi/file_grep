#!/bin/bash
#
# Copyright 2022-2023 Panasonic Corporation
#

cd ../../../work/${MACHINE}-poky-linux/imx-boot/1.0-r0/git
PATH_BOOTBIN=$(pwd)

#Get SPL & FIT offset, authaddr
make SOC=iMX8MN flash_hdmi_spl_uboot &> makelog.txt
OFF_ADDR=($(grep -e "csf_off" -e "hab block" makelog.txt))

#Get FIT authaddr 2-5
make SOC=iMX8MN print_fit_hab > makelog2.txt
FIT_ADDR2_5=($(grep 0x makelog2.txt))

rm makelog.txt
rm makelog2.txt

#Get kernel load address
cd ../../../u-boot-imx/2022.04-r0/git/include/configs
KLOADADDR=($(cat imx8mn_pew.h | grep "#define CONFIG_LOADADDR"))

cd ../../../../../../../deploy/images/${MACHINE}
PATH_KERNELBIN=$(pwd)

#Get kernel load size
DUMPDATA=($(od -x -j 0x10 -N 0x4 --endian=little Image))
KLOADSIZE="0x"${DUMPDATA[2]}${DUMPDATA[1]}

echo "#These data are for the CSF Description File & other" > CSFDescData.txt
echo "SPL_Auth_Off ${OFF_ADDR[1]}" >> CSFDescData.txt
echo "SPL_Auth_Addr ${OFF_ADDR[5]} ${OFF_ADDR[6]} ${OFF_ADDR[7]}" >> CSFDescData.txt
echo "FIT_Auth_Off ${OFF_ADDR[9]}" >> CSFDescData.txt
echo "FIT_Auth_Addr_1 ${OFF_ADDR[13]} ${OFF_ADDR[14]} ${OFF_ADDR[15]}" >> CSFDescData.txt
echo "FIT_Auth_Addr_2 ${FIT_ADDR2_5[6]} ${FIT_ADDR2_5[7]} ${FIT_ADDR2_5[8]}" >> CSFDescData.txt
echo "FIT_Auth_Addr_3 ${FIT_ADDR2_5[9]} ${FIT_ADDR2_5[10]} ${FIT_ADDR2_5[11]}" >> CSFDescData.txt
echo "FIT_Auth_Addr_4 ${FIT_ADDR2_5[12]} ${FIT_ADDR2_5[13]} ${FIT_ADDR2_5[14]}" >> CSFDescData.txt
echo "FIT_Auth_Addr_5 ${FIT_ADDR2_5[15]} ${FIT_ADDR2_5[16]} ${FIT_ADDR2_5[17]}" >> CSFDescData.txt
echo "Kernel_Load_Addr ${KLOADADDR[2]}" >> CSFDescData.txt
echo "Kernel_Load_Size $KLOADSIZE" >> CSFDescData.txt
echo "Kernel_Pad_Size" $(printf '0x%08x' $(($KLOADSIZE+0x20))) >> CSFDescData.txt
echo "#File Path" >> CSFDescData.txt
echo "SPL_FIT_Path $PATH_BOOTBIN/iMX8M/flash.bin" >> CSFDescData.txt
echo "Kernel_Path $PATH_KERNELBIN/Image_pad_ivt.bin" >> CSFDescData.txt
echo "Image_Path $PATH_KERNELBIN" >> CSFDescData.txt
echo "Created \"CSFDescData.txt\"."


