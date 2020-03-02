#!/bin/bash
set -e
export MACOSX_DEPLOYMENT_TARGET=10.9
export CMAKE_OSX_DEPLOYMENT_TARGET=10.9
export CMAKE_OSX_ARCHITECTURES="x86_64"
export UAMQP_USE_OPENSSL=True
export UAMQP_REBUILD_PYX=True
export UAMQP_SUPPRESS_LINK_FLAGS=True
export OPENSSL_ROOT_DIR="/tmp/openssl"
export OPENSSL_INCLUDE_DIR="/tmp/openssl/include"
export LDFLAGS="-mmacosx-version-min=10.9 -L/tmp/openssl/lib"
export CFLAGS="-mmacosx-version-min=10.9 -I/tmp/openssl/include"

python2.7 setup.py bdist_wheel
python3.4 setup.py bdist_wheel
python3.5 setup.py bdist_wheel
python3.6 setup.py bdist_wheel
python3.7 setup.py bdist_wheel
python3.8 setup.py bdist_wheel
