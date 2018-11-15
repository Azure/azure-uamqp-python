#!/bin/bash

# Modified from https://gist.github.com/tmiz/1441111

curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_i386
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_x86_64
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION $AGENT_TEMPDIRECTORY/openssl
cd openssl_i386
./Configure darwin-i386-cc shared --openssldir=/private/etc/ssl
make
cd ../
cd openssl_x86_64
./Configure darwin64-x86_64-cc shared --openssldir=/private/etc/ssl
make
cd ../
cp -a ./openssl_x86_64/. $AGENT_TEMPDIRECTORY/openssl/
mkdir $AGENT_TEMPDIRECTORY/openssl/lib
lipo -create openssl_i386/libcrypto.a openssl_x86_64/libcrypto.a -output $AGENT_TEMPDIRECTORY/openssl/lib/libcrypto.a
lipo -create openssl_i386/libssl.a openssl_x86_64/libssl.a -output $AGENT_TEMPDIRECTORY/openssl/lib/libssl.a
rm openssl-$OPENSSL_VERSION.tar.gz
