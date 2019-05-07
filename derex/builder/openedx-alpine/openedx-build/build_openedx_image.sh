#!/bin/sh

# Build an image good for deployment of openedx

set -e
DIR=$(dirname $(readlink -f "$0"))
. "${DIR}/variables.sh"
set -x

checkout_edx_platform

if (buildah images|grep ^localhost/${IMAGE_BASENAME}\ ); then
    echo '\e[1;32m'Not building ${IMAGE_BASENAME}: already built'\e[0m'
else
    CONTAINER=$(buildah from ${IMAGE_WHEELS})

    buildah copy $CONTAINER $DIR/container_scripts/* /openedx/bin/
    buildah copy $CONTAINER $DIR/container_scripts/build_openedx_node.sh /openedx/bin/
    buildah copy $CONTAINER $DIR/settings/lms /openedx/edx-platform/lms/envs/derek
    buildah copy $CONTAINER $DIR/settings/cms /openedx/edx-platform/cms/envs/derek
    buildah copy $CONTAINER $DIR/gunicorn_conf.py /openedx/
    # Build wheels and install them
    buildah copy $CONTAINER ${EDX_PLATFORM_PATH} /openedx/edx-platform
    buildah run -v $APK_CACHE:/var/cache/apk $CONTAINER apk add gettext
    buildah run -v $PIP_CACHE:/root/.cache/pip $CONTAINER /openedx/bin/install_openedx.sh
    buildah run -v $NPM_CACHE:/root/.npm $CONTAINER /openedx/bin/build_openedx_node.sh
    buildah config \
        --author='Silvio Tomatis' \
        --entrypoint '["/openedx/bin/docker-entrypoint.sh"]' \
        --cmd '/bin/sh -c "gunicorn -c /openedx/gunicorn_conf.py --name ${SERVICE_VARIANT} --bind=0.0.0.0:8000 --max-requests=1000 ${SERVICE_VARIANT}.wsgi:application"' \
        --workingdir='/openedx/edx-platform' \
        --env CONFIG_ROOT=/openedx/config \
        --env PATH=/openedx/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        --env SERVICE_VARIANT=lms \
        --env SETTINGS=derek.production \
        --env DOCKERIZE_VERSION=$DOCKERIZE_VERSION \
        $CONTAINER

    buildah commit --rm $CONTAINER ${IMAGE_BASENAME}
    echo Built wheel image '\e[1;32m'${IMAGE_BASENAME}'\e[0m'.
fi
