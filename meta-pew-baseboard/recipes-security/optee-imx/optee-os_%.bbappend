# Copyright 2022-2023 Panasonic Corporation

FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://0001-change-ddr-size.patch"

EXTRA_OEMAKE += " PEW_BOARD_TYPE=${MACHINE} "
