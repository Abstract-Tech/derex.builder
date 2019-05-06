#!/bin/sh

cp /sbin/ldconfig /sbin/ldconfig.orig

(echo -e '#!/bin/sh
if [ "$1" = "-p" ]; then
    # Hack to mimic GNU ldconfig s -p option, needed by ctypes, used by shapely
    echo "    libc.musl-x86_64.so.1 (libc6,x86-64) => /lib/libc.musl-x86_64.so.1"
    exit 0
fi
' ; tail -n +2 /sbin/ldconfig.orig) > /sbin/ldconfig
