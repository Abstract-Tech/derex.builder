#!/bin/sh
set -e
set -x

EDX_PLATFORM_REPOSITORY=https://github.com/edx/edx-platform.git
EDX_PLATFORM_VERSION=open-release/ironwood.1

mkdir -p /openedx/themes /openedx/locale /openedx/bin/
mv /tmp/openedx-assets /openedx/bin/

wget -O - https://github.com/regisb/openedx-i18n/archive/hawthorn.tar.gz \
    |tar xzf - --strip-components=3 --directory /openedx/locale/ openedx-i18n-hawthorn/edx-platform/locale/

git clone ${EDX_PLATFORM_REPOSITORY} --branch ${EDX_PLATFORM_VERSION} --depth 1 /openedx/edx-platform
cd /openedx/edx-platform

pip install --src /openedx/packages -r requirements/edx/base.txt
find /openedx/ -type d -name .git -exec rm -r {} +  # 70 Mb

# Copy the assets.py config file in place
mkdir -p /openedx/edx-platform/lms/envs/derex /openedx/edx-platform/cms/envs/derex
cp /tmp/assets.py /openedx/edx-platform/lms/envs/derex
echo > /openedx/edx-platform/lms/envs/derex/__init__.py
mv /tmp/assets.py /openedx/edx-platform/cms/envs/derex
echo > /openedx/edx-platform/cms/envs/derex/__init__.py

# We prefer to do all tasks required for execution in advance,
# so we accept the additional 57 Mb this brings
python -m compileall /openedx  # +57 Mb
