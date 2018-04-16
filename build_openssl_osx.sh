#!/bin/bash

export OPENSSL_VERSION="1.0.2n"
export MACOSX_DEPLOYMENT_TARGET=10.6

# Modified from https://gist.github.com/tmiz/1441111

curl -O http://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_i386_src
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_x86_64_src
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl
cd openssl_i386_src
./Configure darwin-i386-cc shared --openssldir=/private/etc/ssl --prefix=/tmp/openssl_i386
make
make install
cd ../
cd openssl_x86_64_src
./Configure darwin64-x86_64-cc shared --openssldir=/private/etc/ssl --prefix=/tmp/openssl_x86_64
make
make install
cd ../
mkdir openssl
cp -a ./openssl_x86_64/. ./openssl/
lipo -create openssl_i386/lib/libcrypto.a openssl_x86_64/lib/libcrypto.a -output openssl/lib/libcrypto.a
lipo -create openssl_i386/lib/libssl.a openssl_x86_64/lib/libssl.a -output openssl/lib/libssl.a
rm openssl-$OPENSSL_VERSION.tar.gz