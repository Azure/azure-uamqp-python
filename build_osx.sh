#!/bin/bash
set -e

export UAMQP_VERSION="0.1.0a3"
export MACOSX_DEPLOYMENT_TARGET=10.6
export UAMQP_SUPPRESS_LINK_FLAGS=True
export CEF_CCFLAGS="-arch x86_64"
export LDFLAGS="$(brew --prefix openssl@1.1)/lib/libssl.a $(brew --prefix openssl@1.1)/lib/libcrypto.a"
export LDFLAGS="$LDFLAGS $(brew --prefix ossp-uuid)/lib/libuuid.a" 
export CFLAGS="-I$(brew --prefix openssl@1.1)/include"

# Make sure Cython and Wheel are available in all env
python3.4 -m pip install cython==0.27.3 wheel
python3.5 -m pip install cython==0.27.3 wheel
python3.6 -m pip install cython==0.27.3 wheel

python3.4 setup.py bdist_wheel
python3.5 setup.py bdist_wheel
python3.6 setup.py bdist_wheel
