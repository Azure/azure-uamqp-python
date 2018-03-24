#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v $PWD:/data ubuntu /data/build_linux_sdist.sh

export UAMQP_VERSION="0.1.0b1"

apt-get update
apt-get install -y build-essential libssl-dev python3-dev uuid-dev cmake python3-pip

cd /data
pip3 install --upgrade pip
pip3 install cython wheel
python3 setup.py sdist