# Copyright 2022-2023 Panasonic Corporation

do_configure:append() {
    sed -i -e "s/CONFIG_PCIE8997=y/CONFIG_PCIE8997=n/g" ${S}/Makefile
    sed -i -e "s/CONFIG_PCIE9098=y/CONFIG_PCIE9098=n/g" ${S}/Makefile
}
