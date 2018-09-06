#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v $PWD:/data local/armv7l /data/build_armv7l.sh
# docker run --rm -v $PWD:/data local/armv7l_wheezy /data/build_armv7l.sh

export UAMQP_VERSION="1.0.2"
export CPATH="/opt/uamqp/openssl/include"
export LIBRARY_PATH="/opt/uamqp/openssl/lib"
export OPENSSL_ROOT_DIR="/opt/uamqp/openssl"
export OPENSSL_INCLUDE_DIR="/opt/uamqp/openssl/include"
export UAMQP_SUPPRESS_LINK_FLAGS=True
export LDFLAGS="-L/opt/uamqp/openssl/lib/libssl.a -L/opt/uamqp/openssl/lib/libcrypto.a"
export CFLAGS="-I/opt/uamqp/openssl/include"

# Build the wheels
pushd /data
#/usr/local/bin/python3.4 setup.py bdist_wheel
/usr/local/bin/python3.5 setup.py bdist_wheel
auditwheel repair -w /data/wheelhouse dist/uamqp-${UAMQP_VERSION}-cp35-cp35m-linux_armv7l.whl
#/usr/local/bin/python3.6 setup.py bdist_wheel --plat linux_armv7l
#/usr/local/bin/python3.7 setup.py bdist_wheel