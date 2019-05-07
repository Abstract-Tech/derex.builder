#!/bin/sh

# Build an image including all dependencies needed to build openedx

set -e
DIR=$(dirname $(readlink -f "$0"))
. "${DIR}/variables.sh"
set -x

CONTAINER=$(buildah from python:2-alpine3.7)

buildah config \
    --env DOCKERIZE_VERSION=$DOCKERIZE_VERSION \
    $CONTAINER

# Copy our scripts to the container
buildah copy $CONTAINER $DIR/container_scripts/install_run_dependencies.sh /openedx/bin/

# Install dependencies with package manager
buildah run -v $APK_CACHE:/var/cache/apk $CONTAINER -- /openedx/bin/install_run_dependencies.sh

buildah commit --rm $CONTAINER ${IMAGE_BASE}

echo Built base runtime image '\e[1;32m'${IMAGE_BASE}'\e[0m'.
