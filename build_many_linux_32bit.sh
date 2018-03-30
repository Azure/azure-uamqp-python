#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v $PWD:/data pyca/cryptography-manylinux1:i686 /data/build_many_linux_32bit.sh

export UAMQP_VERSION="0.1.0b2"

export CPATH="/opt/pyca/cryptography/openssl/include"
export LIBRARY_PATH="/opt/pyca/cryptography/openssl/lib"

# Build libuuid
pushd /tmp
wget https://www.kernel.org/pub/linux/utils/util-linux/v2.27/util-linux-2.27.1.tar.gz --no-check-certificate
tar xvf util-linux-2.27.1.tar.gz
cd util-linux-2.27.1
./configure --disable-shared --disable-all-programs --enable-libuuid CFLAGS=-fPIC
make
make install
popd

# Make sure Cython and Wheel are available in all env
/opt/python/cp34-cp34m/bin/python -m pip install cython==0.27.3 wheel
/opt/python/cp35-cp35m/bin/python -m pip install cython==0.27.3 wheel
/opt/python/cp36-cp36m/bin/python -m pip install cython==0.27.3 wheel

# Build the wheels
pushd /data
/opt/python/cp34-cp34m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp34-cp34m-linux_i686.whl

/opt/python/cp35-cp35m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp35-cp35m-linux_i686.whl

/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp36-cp36m-linux_i686.whl
