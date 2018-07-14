#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v $PWD:/data local/manylinux_crypto64 /data/build_many_linux_64bit.sh

export UAMQP_VERSION="0.1.1"

export CPATH="/opt/pyca/cryptography/openssl/include"
export LIBRARY_PATH="/opt/pyca/cryptography/openssl/lib"
export OPENSSL_ROOT_DIR="/opt/pyca/cryptography/openssl"

# Make sure Cython and Wheel are available in all env
/opt/python/cp34-cp34m/bin/python -m pip install cython==0.28.4 wheel
/opt/python/cp35-cp35m/bin/python -m pip install cython==0.28.4 wheel
/opt/python/cp36-cp36m/bin/python -m pip install cython==0.28.4 wheel
/opt/python/cp37-cp37m/bin/python -m pip install cython==0.28.4 wheel

# Build the wheels
pushd /data
/opt/python/cp34-cp34m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp34-cp34m-linux_x86_64.whl

/opt/python/cp35-cp35m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp35-cp35m-linux_x86_64.whl

/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp36-cp36m-linux_x86_64.whl

/opt/python/cp37-cp37m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp37-cp37m-linux_x86_64.whl
