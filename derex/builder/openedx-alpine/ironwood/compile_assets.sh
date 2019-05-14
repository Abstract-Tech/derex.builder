#!/bin/sh
set -e
set -x

apk add nodejs
nodeenv /openedx/nodeenv --node=8.9.3 --prebuilt

cd /openedx/edx-platform
/openedx/nodeenv/bin/npm set progress=false
/openedx/nodeenv/bin/npm install
echo 'PATH=/openedx/edx-platform/node_modules/.bin:/openedx/nodeenv/bin:/openedx/bin:${PATH}'>>~/.profile

. ~/.profile
cd /openedx/edx-platform
openedx-assets xmodule
openedx-assets npm
openedx-assets webpack --env=prod
openedx-assets common

openedx-assets themes
openedx-assets collect --settings=derek.assets

# Free up some space
rm -r \
    /openedx/nodeenv/ `# 137.3M` \
    /openedx/edx-platform/node_modules/ `# 368.9M` \
    /openedx/staticfiles/*/node_modules `# 54.2M`
apk del nodejs # 52M
