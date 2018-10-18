#!/bin/bash
set -e

# To execute this script:
# docker run --rm -v %cd%:/data --entrypoint="/bin/bash" -e "UAMQP_REBUILD_PYX=True" fnndsc/ubuntu-python3 /data/build_linux_sdist.sh

apt-get update
apt-get install -y build-essential libssl-dev uuid-dev cmake libcurl4-openssl-dev pkg-config

cd /data
pip3 install cython==0.28.5 wheel
python3 setup.py sdist