# Copyright 2022-2023 Panasonic Corporation

FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

RDEPENDS:${PN}:remove = "kernel-tools-pci"

