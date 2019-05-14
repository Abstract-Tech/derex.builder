#!/bin/sh
set -e
set -x

EDX_PLATFORM_REPOSITORY=https://github.com/edx/edx-platform.git
EDX_PLATFORM_VERSION=open-release/ironwood.1

mkdir -p /openedx/themes /openedx/locale

wget -O - https://github.com/regisb/openedx-i18n/archive/hawthorn.tar.gz \
    |tar xzf - --strip-components=3 --directory /openedx/locale/ openedx-i18n-hawthorn/edx-platform/locale/

git clone ${EDX_PLATFORM_REPOSITORY} --branch ${EDX_PLATFORM_VERSION} --depth 1 /openedx/edx-platform
cd /openedx/edx-platform

pip install --src /openedx/packages -r requirements/edx/base.txt
find /openedx/ -type d -name .git -exec rm -r {} +  # 70 Mb

# We prefer to do all tasks required for execution in advance,
# so we accept the additional 57 Mb this brings
python -m compileall /openedx  # +57 Mb
