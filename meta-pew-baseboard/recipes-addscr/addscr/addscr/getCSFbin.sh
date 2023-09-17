#!/bin/bash
#
# Copyright 2022 Panasonic Corporation
#

# CSTフォルダ存在チェック
RET=`ls ../../../../../ | grep ^cst-*`
if [ $? -ne 0 ]; then
    # フォルダが存在しない場合
    echo "Error:CST tool not found."
    echo "Put CST tool in the same directory."
    exit 1
fi

# 必要な情報を取得して、tmpフォルダに移動
SPL_AUTHADDR=($(cat CSFDescData.txt | grep SPL_Auth_Addr))
SPLFIT_TARGETPATH=($(cat CSFDescData.txt | grep SPL_FIT_Path))
FIT_AUTHADDR1=($(cat CSFDescData.txt | grep FIT_Auth_Addr_1))
FIT_AUTHADDR2=($(cat CSFDescData.txt | grep FIT_Auth_Addr_2))
FIT_AUTHADDR3=($(cat CSFDescData.txt | grep FIT_Auth_Addr_3))
FIT_AUTHADDR4=($(cat CSFDescData.txt | grep FIT_Auth_Addr_4))
FIT_AUTHADDR5=($(cat CSFDescData.txt | grep FIT_Auth_Addr_5))
KNL_LOADADDR=($(cat CSFDescData.txt | grep Kernel_Load_Addr))
KNL_PADSIZE=($(cat CSFDescData.txt | grep Kernel_Pad_Size))
KNL_TARGETPATH=($(cat CSFDescData.txt | grep Kernel_Path))
IMG_PATH=($(cat CSFDescData.txt | grep Image_Path))

cd ../../../../../${RET}/tmp
if [ $? -ne 0 ]; then
    # フォルダに移動できない場合
    exit 1
fi

# CSF記述ファイル存在チェック
grep -q "/[Authenticate Data/]" csf_spl.txt
if [ $? -ne 0 ]; then
    exit 1
fi

grep -q "/[Authenticate Data/]" csf_fit.txt
if [ $? -ne 0 ]; then
    exit 1
fi

grep -q "/[Authenticate Data/]" csf_additional_images.txt
if [ $? -ne 0 ]; then
    exit 1
fi

# SPLのCSF記述ファイルを更新
sed -e "s|Blocks = .*|Blocks = ${SPL_AUTHADDR[1]} ${SPL_AUTHADDR[2]} ${SPL_AUTHADDR[3]} \"${SPLFIT_TARGETPATH[1]}\"|g" \
    -i csf_spl.txt

# FITのCSF記述ファイルを更新
# 毎回5行分書き換えるため先に終端4行を削除
sed -e '$d' -i csf_fit.txt
sed -e '$d' -i csf_fit.txt
sed -e '$d' -i csf_fit.txt
sed -e '$d' -i csf_fit.txt
sed -e "s|Blocks = .*|Blocks = ${FIT_AUTHADDR1[1]} ${FIT_AUTHADDR1[2]} ${FIT_AUTHADDR1[3]} \"${SPLFIT_TARGETPATH[1]}\", \\\\\n    ${FIT_AUTHADDR2[1]} ${FIT_AUTHADDR2[2]} ${FIT_AUTHADDR2[3]} \"${SPLFIT_TARGETPATH[1]}\", \\\\\n    ${FIT_AUTHADDR3[1]} ${FIT_AUTHADDR3[2]} ${FIT_AUTHADDR3[3]} \"${SPLFIT_TARGETPATH[1]}\", \\\\\n    ${FIT_AUTHADDR4[1]} ${FIT_AUTHADDR4[2]} ${FIT_AUTHADDR4[3]} \"${SPLFIT_TARGETPATH[1]}\", \\\\\n    ${FIT_AUTHADDR5[1]} ${FIT_AUTHADDR5[2]} ${FIT_AUTHADDR5[3]} \"${SPLFIT_TARGETPATH[1]}\"|g" \
    -i csf_fit.txt

# KernelのCSF記述ファイルを更新
sed -e "s|Blocks = .*|Blocks = ${KNL_LOADADDR[1]} 0x0 ${KNL_PADSIZE[1]} \"${KNL_TARGETPATH[1]}\"|g" \
    -e "s|^\t\s\{4,\}.*||g" \
    -i csf_additional_images.txt

# 署名ファイル作成
../linux64/bin/cst -i csf_spl.txt --o ../csf_spl.bin
../linux64/bin/cst -i csf_fit.txt --o ../csf_fit.bin
../linux64/bin/cst -i csf_additional_images.txt --o ../csf_Image.bin

# 作成した署名ファイルをビルド環境に移動
mv ../csf_spl.bin ${IMG_PATH[1]}/
mv ../csf_fit.bin ${IMG_PATH[1]}/
mv ../csf_Image.bin ${IMG_PATH[1]}/
