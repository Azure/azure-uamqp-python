#!/bin/bash

# Modified from https://gist.github.com/tmiz/1441111

export DEST="$AGENT_TEMPDIRECTORY/openssl"
# Acquire sources
curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
rm -f openssl-$OPENSSL_VERSION.tar.gz

# Set up two build environments
cp -R openssl-$OPENSSL_VERSION openssl_i386_src
mv openssl-$OPENSSL_VERSION openssl_x86_64_src

# Compile i386
cd openssl_i386_src
./Configure darwin-i386-cc no-ssl2 no-ssl3 no-zlib no-shared no-comp --prefix=$DEST/openssl --openssldir=$DEST/openssl
make depend
make
make install
mv $DEST/openssl $DEST/openssl_i386

# Compile x86_64
cd ../openssl_x86_64_src
./Configure darwin64-x86_64-cc enable-ec_nistp_64_gcc_128 no-ssl2 no-ssl3 no-zlib no-shared no-comp --prefix=$DEST/openssl --openssldir=$DEST/openssl
make depend
make
make install
mv $DEST/openssl $DEST/openssl_x86_64

# Move files into place and generate universal binaries
cd $DEST
cp -a ./openssl_x86_64/. ./openssl/
lipo -create openssl_i386/lib/libcrypto.a openssl_x86_64/lib/libcrypto.a -output openssl/lib/libcrypto.a
lipo -create openssl_i386/lib/libssl.a openssl_x86_64/lib/libssl.a -output openssl/lib/libssl.a
