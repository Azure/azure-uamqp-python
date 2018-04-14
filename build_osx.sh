#!/bin/bash
set -e
export MACOSX_DEPLOYMENT_TARGET=10.6
export UAMQP_NO_OPENSSL=False
export CMAKE_OSX_DEPLOYMENT_TARGET=10.6
export CMAKE_OSX_ARCHITECTURES="i386;x86_64"
export UAMQP_SUPPRESS_LINK_FLAGS=True
export LDFLAGS="$(brew --prefix openssl@1.0)/lib/libssl.a $(brew --prefix openssl@1.0)/lib/libcrypto.a"
export CFLAGS="-I$(brew --prefix openssl@1.0)/include"

# Make sure Cython and Wheel are available in all env
python3.4 -m pip install cython==0.27.3 wheel
python3.5 -m pip install cython==0.27.3 wheel
python3.6 -m pip install cython==0.27.3 wheel

python3.4 setup.py bdist_wheel
python3.5 setup.py bdist_wheel
python3.6 setup.py bdist_wheel
