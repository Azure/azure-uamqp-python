#!/bin/bash
set -e
export MACOSX_DEPLOYMENT_TARGET=10.6
export CMAKE_OSX_DEPLOYMENT_TARGET=10.6
export CMAKE_OSX_ARCHITECTURES="i386;x86_64"
export UAMQP_USE_OPENSSL=True
export UAMQP_SUPPRESS_LINK_FLAGS=True
export OPENSSL_ROOT_DIR="/tmp/openssl"
export OPENSSL_INCLUDE_DIR="/tmp/openssl/include"
export LDFLAGS="/tmp/openssl/lib/libssl.a /tmp/openssl/lib/libcrypto.a"
export CFLAGS="-I/tmp/openssl/include"

python3.4 setup.py bdist_wheel
python3.5 setup.py bdist_wheel
python3.6 setup.py bdist_wheel
python3.7 setup.py bdist_wheel
