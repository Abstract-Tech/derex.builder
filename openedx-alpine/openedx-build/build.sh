#!/bin/sh
set -e
set -x

DIR=$(dirname $(readlink -f "$0"))
. "${DIR}/variables.sh"

mkdir -p ${PIP_CACHE}
mkdir -p ${APK_CACHE}
mkdir -p ${NPM_CACHE}


"${DIR}/build_base.sh"

"${DIR}/build_buildwheels.sh"

"${DIR}/build_wheels.sh"

"${DIR}/build_openedx_image.sh"

buildah push ${IMAGE_BASENAME} docker-daemon:silviot/${IMAGE_BASENAME}:ironwood
