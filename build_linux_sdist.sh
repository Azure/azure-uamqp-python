#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v %cd%:/data --entrypoint="/bin/bash" fnndsc/ubuntu-python3 /data/build_linux_sdist.sh

export UAMQP_VERSION="0.1.0b2"

apt-get update
apt-get install -y build-essential libssl-dev uuid-dev cmake libcurl4-openssl-dev pkg-config

cd /data
pip3 install cython wheel
python3 setup.py sdist