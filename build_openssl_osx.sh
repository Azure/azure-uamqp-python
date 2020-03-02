#!/bin/bash

# Acquire sources
curl -sSO https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
tar -xzf openssl-$OPENSSL_VERSION.tar.gz
rm -f openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_src

# Compile x86_64
cd openssl_src
./Configure darwin64-x86_64-cc enable-ec_nistp_64_gcc_128 no-ssl2 no-ssl3 no-zlib no-shared no-comp --prefix=$DEST/openssl --openssldir=$DEST/openssl
make depend
make
make install_sw

# Move files into place
cd $DEST
mv openssl/lib/libcrypto.a openssl/lib/libazcrypto.a
mv openssl/lib/libssl.a openssl/lib/libazssl.a
