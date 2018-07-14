#!/bin/bash

export OPENSSL_VERSION="1.0.2o"

curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_armv7l_src

cd openssl_armv7l_src
./Configure linux-armv4 shared --prefix=/opt/uamqp/openssl
make
make install
rm openssl-$OPENSSL_VERSION.tar.gz