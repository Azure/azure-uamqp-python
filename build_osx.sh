#!/bin/bash
set -e
export MACOSX_DEPLOYMENT_TARGET=10.6

# Make sure Cython and Wheel are available in all env
python3.4 -m pip install cython==0.27.3 wheel
python3.5 -m pip install cython==0.27.3 wheel
python3.6 -m pip install cython==0.27.3 wheel

python3.4 setup.py bdist_wheel
python3.5 setup.py bdist_wheel
python3.6 setup.py bdist_wheel
