#!/bin/sh
set -e
set -x

DOCKERIZE_VERSION=${DOCKERIZE_VERSION:-v0.6.1}
wget -q -O - "https://github.com/jwilder/dockerize/releases/download/${DOCKERIZE_VERSION}/dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz" | tar xzf - --directory /usr/local/bin

echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories

apk add \
    geos-dev@testing \
    gettext \
    git \
    graphviz \
    freetype \
    graphviz \
    lapack \
    libjpeg \
    libxslt \
    mariadb-common \
    sqlite \
    xmlsec
