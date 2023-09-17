# Copyright 2022-2023 Panasonic Corporation

compile_mx8mn:append() {
    cp ${DEPLOY_DIR_IMAGE}/${BOOT_TOOLS}/${UBOOT_DTB_NAME}   ${BOOT_STAGING}/imx8mn-evk.dtb
}
