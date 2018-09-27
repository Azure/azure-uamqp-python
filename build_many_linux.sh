#!/bin/bash
set -e

# Inspired by https://github.com/pypa/python-manylinux-demo/blob/a615d78e5042c01a03e1bbb1ca78603c90dbce1f/travis/build-wheels.sh

# To build 32bit wheels, run:
# docker run --rm -v $PWD:/data local/manylinux_crypto32 /data/build_many_linux.sh
# To build 64bit wheels, run:
# docker run --rm -v $PWD:/data local/manylinux_crypto64 /data/build_many_linux.sh

export UAMQP_VERSION="1.1.0rc1"

export CPATH="/opt/pyca/cryptography/openssl/include"
export LIBRARY_PATH="/opt/pyca/cryptography/openssl/lib"
export OPENSSL_ROOT_DIR="/opt/pyca/cryptography/openssl"

# Build the wheels
cd /data
for PYBIN in /opt/python/*/bin; do
	$PYBIN/pip install cython==0.28.4 wheel;
	$PYBIN/python setup.py bdist_wheel -d /wheelhouse;
	rm -rf build/
done;

# Repair the wheels
for WHL in /wheelhouse/*; do
	auditwheel repair $WHL -w /data/wheelhouse/;
done;
