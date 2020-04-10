#!/bin/bash
set -e
export MACOSX_DEPLOYMENT_TARGET=10.9
export CMAKE_OSX_DEPLOYMENT_TARGET=10.9
export CMAKE_OSX_ARCHITECTURES="x86_64"
export UAMQP_REBUILD_PYX=True
export LDFLAGS="-mmacosx-version-min=10.9"
export CFLAGS="-mmacosx-version-min=10.9"

python2.7 setup.py bdist_wheel
python3.4 setup.py bdist_wheel
python3.5 setup.py bdist_wheel
python3.6 setup.py bdist_wheel
python3.7 setup.py bdist_wheel
python3.8 setup.py bdist_wheel
