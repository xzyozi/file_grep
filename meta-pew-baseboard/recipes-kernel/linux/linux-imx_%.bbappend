# Copyright 2023 Panasonic Corporation

FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-linux-imx8mn-pew.patch \
    file://imx8mn-pew-mon-defconfig \
    file://imx8mn-pew-gw-defconfig \
    file://imx8mn-pew-bizgw-defconfig \
"

IMX_KERNEL_CONFIG_AARCH64:imx8mnpewmon= "imx8mn-pew-mon-defconfig"
IMX_KERNEL_CONFIG_AARCH64:imx8mnpewgw= "imx8mn-pew-gw-defconfig"
IMX_KERNEL_CONFIG_AARCH64:imx8mnpewbizgw= "imx8mn-pew-bizgw-defconfig"

do_kernel_metadata:prepend() {
   case "${MACHINE}" in
       imx8mnpewmon)
           cp ${WORKDIR}/imx8mn-pew-mon-defconfig ${S}/arch/arm64/configs/
           ;;
       imx8mnpewgw)
           cp ${WORKDIR}/imx8mn-pew-gw-defconfig ${S}/arch/arm64/configs/
           ;;
       imx8mnpewbizgw)
           cp ${WORKDIR}/imx8mn-pew-bizgw-defconfig ${S}/arch/arm64/configs/
           ;;
       *)
           ;;
   esac
}
