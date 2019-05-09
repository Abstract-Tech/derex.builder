export IMAGE_BASENAME=${IMAGE_BASENAME:-openedx}

export EDX_PLATFORM_REPOSITORY=https://github.com/edx/edx-platform.git
export EDX_PLATFORM_VERSION=open-release/ironwood.1

IMAGE_BASENAME=${IMAGE_BASENAME:-openedx-alpine}
IMAGE_BUILDWHEELS=${IMAGE_BUILDWHEELS:-${IMAGE_BASENAME}-buildwheels}
IMAGE_BASE=${IMAGE_BASE:-${IMAGE_BASENAME}-base}
IMAGE_WHEELS=${IMAGE_WHEELS:-${IMAGE_BASENAME}-wheels}

PIP_CACHE=${PIP_CACHE:-/var/cache/pip-alpine}
APK_CACHE=${APK_CACHE:-/var/cache/apk}
NPM_CACHE=${NPM_CACHE:-/var/cache/npm}

export DOCKERIZE_VERSION=${DOCKERIZE_VERSION:-v0.6.1}

if [ $(id -u) != '0' ]; then
    alias buildah='sudo buildah'
fi

DIR=$(dirname $(readlink -f "$0"))

# A git proxy can be run with
# docker run --name gitcache -d --rm -p 8080:8080 -v /var/cache/git:/tmp/cache/git kurzdigital/git-cache-http-server
# and an environment variable can be set, like:
# export GIT_CACHE_PROXY_URL=http://172.17.0.1:8080/
# note it should include protocol and trailing slash

if [ -z "$GIT_CACHE_PROXY_URL" ] && (curl -s localhost:8080 -I|grep -q 500\ Internal\ Server\ Err); then
    GIT_CACHE_PROXY_URL=http://172.17.0.1:8080/
fi


# Setup git cache if configured
if [ ! -z "$GIT_CACHE_PROXY_URL" ] ; then
    buildah run $CONTAINER -- git config --global url."$GIT_CACHE_PROXY_URL".insteadOf https://
fi
EDX_PLATFORM_PATH=${DIR}/../edx-platform
checkout_edx_platform () {
    if [ ! -d ${EDX_PLATFORM_PATH} ]; then
        git clone ${EDX_PLATFORM_REPOSITORY} --branch ${EDX_PLATFORM_VERSION} --depth 1 ${EDX_PLATFORM_PATH}
    else
        cd ${EDX_PLATFORM_PATH}
        git checkout ${EDX_PLATFORM_VERSION}
        git pull
        cd -
    fi
}
