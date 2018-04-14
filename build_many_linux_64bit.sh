#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v %cd%:/data local/manylinux64 /data/build_many_linux_64bit.sh

export UAMQP_VERSION="0.1.0b3"

export CPATH="/etc/ssl/include"
export LIBRARY_PATH="/etc/ssl/lib"
export LD_LIBRARY_PATH="/etc/ssl/lib"
export OPENSSL_ROOT_DIR="/etc/ssl"

# Build libuuid
#pushd /tmp
#curl -O https://cdn.kernel.org/pub/linux/utils/util-linux/v2.27/util-linux-2.27.1.tar.gz
#tar xvf util-linux-2.27.1.tar.gz
#cd util-linux-2.27.1
#./configure --disable-shared --disable-all-programs --enable-libuuid CFLAGS=-fPIC
#make
#make install
#popd

# Build OpenSSL
pushd /tmp
cd openssl-1.0.2n
./config shared --openssldir=/etc/ssl
make depend
make
make install
cp /etc/ssl/lib/*.a /usr/local/lib64/
cp /etc/ssl/lib/*.so.* /usr/local/lib64/
popd

# Make sure Cython and Wheel are available in all env
/opt/python/cp34-cp34m/bin/python -m pip install cython==0.27.3 wheel
/opt/python/cp35-cp35m/bin/python -m pip install cython==0.27.3 wheel
/opt/python/cp36-cp36m/bin/python -m pip install cython==0.27.3 wheel

# Build the wheels
pushd /data
/opt/python/cp34-cp34m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp34-cp34m-linux_x86_64.whl

/opt/python/cp35-cp35m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp35-cp35m-linux_x86_64.whl

/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
auditwheel repair dist/uamqp-${UAMQP_VERSION}-cp36-cp36m-linux_x86_64.whl
