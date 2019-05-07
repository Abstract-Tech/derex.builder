#!/bin/sh

# Build an image including wheels for a specific openedx version

set -e
DIR=$(dirname $(readlink -f "$0"))
. "${DIR}/variables.sh"
set -x

checkout_edx_platform

# This container will be used to populate the $PIP_CACHE and then removed.
BUILDER_CONTAINER=$(buildah from ${IMAGE_BUILDWHEELS})

# Copy our scripts to the container
buildah copy $BUILDER_CONTAINER $DIR/container_scripts/install_wheels.sh /openedx/bin/
# Build wheels and install them
buildah run -v $(readlink -f ${DIR}/../edx-platform):/openedx/edx-platform \
            -v $PIP_CACHE:/root/.cache/pip \
        $BUILDER_CONTAINER -- /openedx/bin/install_wheels.sh
# All wheels were generated. We can't remove this container yet, because
# we need to use its /wheelhouse directory.

TARGET_CONTAINER=$(buildah from ${IMAGE_BASE})
# Install wheels built in the previous step
CONTAINER_ROOT=$(buildah mount ${BUILDER_CONTAINER})
buildah run -v $CONTAINER_ROOT/wheelhouse:/wheelhouse ${TARGET_CONTAINER} sh -c 'pip install /wheelhouse/*'

# XXX Fix for shapely. ctypes is not able to find libmusl in Alpine, unless gcc is installed
# To avoid installing such a heavy dependency, we patch /sbin/ldconfig so that when invoked with `-p`
# it will output info about the libmusl location
buildah copy $TARGET_CONTAINER $DIR/container_scripts/patch_ldconfig_to_fix_shapely.sh /openedx/bin/
buildah run $TARGET_CONTAINER /openedx/bin/patch_ldconfig_to_fix_shapely.sh

buildah commit --rm $TARGET_CONTAINER ${IMAGE_WHEELS}
buildah rm $BUILDER_CONTAINER

echo Built wheel image '\e[1;32m'${IMAGE_WHEELS}'\e[0m'.
