# Copyright 2022-2023 Panasonic Corporation

SUMMARY = "Add scripts"
LICENSE = "CLOSED"

FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI = " \
    file://getCSFDescriptionData.sh \
    file://updateScr_genIVT.sh \
    file://paddingKernel.sh \
    file://makeScr_addSignature.sh \
    file://getCSFbin.sh \
    file://prepare_addSignature.sh \
    file://genSecureBootFile.sh \
    file://genIVT.pl \
"

inherit deploy
INHIBIT_DEFAULT_DEPS = "1"

do_deploy() {
    install -d ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/getCSFDescriptionData.sh ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/updateScr_genIVT.sh ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/paddingKernel.sh ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/getCSFbin.sh ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/makeScr_addSignature.sh ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/prepare_addSignature.sh ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/genSecureBootFile.sh ${DEPLOYDIR}
    install -p -m 0755 ${WORKDIR}/genIVT.pl ${DEPLOYDIR}
}
addtask deploy after do_install
