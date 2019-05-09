#!/bin/sh
set -e
set -x

mkdir -p /openedx/themes /openedx/locale

wget -O - https://github.com/regisb/openedx-i18n/archive/hawthorn.tar.gz \
    |tar xzf - --strip-components=3 --directory /openedx/locale/ openedx-i18n-hawthorn/edx-platform/locale/

cd /openedx/edx-platform

# Combine base.txt and development.txt
cat /openedx/edx-platform/requirements/edx/base.txt \
    /openedx/edx-platform/requirements/edx/development.txt \
    |sort|uniq \
    > /openedx/edx-platform/requirements/edx/base+development.txt

# It would be nice to remove the `-e` options, since we're not interested in
# keeping the `.git` directories around. Unfortunately the `setup.py` file of
# xmodule does not specify its `package_data`.

pip install --src /openedx/packages -r requirements/edx/base+development.txt

python -m compileall /openedx
