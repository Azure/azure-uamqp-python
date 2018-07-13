#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v $PWD:/data local/manylinux_crypto32 /data/build_many_linux_32bit.sh

export UAMQP_VERSION="0.1.1"

export CPATH="/opt/uamqp/openssl/include"
export LIBRARY_PATH="/opt/uamqp/openssl/lib"
export OPENSSL_ROOT_DIR="/opt/uamqp/openssl"
export OPENSSL_INCLUDE_DIR="/opt/uamqp/openssl/include"
export UAMQP_SUPPRESS_LINK_FLAGS=True
export LDFLAGS="/opt/uamqp/openssl/lib/libssl.a /opt/uamqp/openssl/lib/libcrypto.a"
export CFLAGS="-I/opt/uamqp/openssl/include"


# Make sure Cython and Wheel are available in all env
/opt/python/cp34-cp34m/bin/python -m pip install cython==0.28.4 wheel
/opt/python/cp35-cp35m/bin/python -m pip install cython==0.28.4 wheel
/opt/python/cp36-cp36m/bin/python -m pip install cython==0.28.4 wheel
/opt/python/cp37-cp37m/bin/python -m pip install cython==0.28.4 wheel

# Build the wheels
pushd /data
/opt/python/cp34-cp34m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp34-cp34m-linux_i686.whl

/opt/python/cp35-cp35m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp35-cp35m-linux_i686.whl

/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp36-cp36m-linux_i686.whl

/opt/python/cp37-cp37m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp37-cp37m-linux_i686.whl