#!/bin/sh
set -e
set -x

EDX_PLATFORM_REPOSITORY=${EDX_PLATFORM_REPOSITORY:-https://github.com/edx/edx-platform.git}
EDX_PLATFORM_VERSION=${EDX_PLATFORM_VERSION-open-release/hawthorn.2}


# Combine base.txt and development.txt
cat /openedx/edx-platform/requirements/edx/base.txt \
    /openedx/edx-platform/requirements/edx/development.txt \
    |sort|uniq \
    |egrep -v '(^-e|^git)' `# exclude code coming from /openedx/edx-platform and from github`\
    > /openedx/base+development.txt

# Install wheels globally and checkout github sources to /openedx/src/
# Scipy will not build if numpy is not installed ¯\_(ツ)_/¯
time pip install numpy -c /openedx/base+development.txt

time pip wheel --wheel-dir=/wheelhouse --src /openedx/src/ -r /openedx/base+development.txt
