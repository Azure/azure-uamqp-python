#!/bin/bash

# Modified from https://gist.github.com/tmiz/1441111

curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_i386_src
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl_x86_64_src
tar -xvzf openssl-$OPENSSL_VERSION.tar.gz
mv openssl-$OPENSSL_VERSION openssl
cd openssl_i386_src
./Configure darwin-i386-cc shared --openssldir=/private/etc/ssl --prefix=$AGENT_TEMPDIRECTORY/openssl_i386
make
make install
cd ../
cd openssl_x86_64_src
./Configure darwin64-x86_64-cc shared --openssldir=/private/etc/ssl --prefix=$AGENT_TEMPDIRECTORY/openssl_x86_64
make
make install
cd ../
cp -a $AGENT_TEMPDIRECTORY/openssl_x86_64/. $AGENT_TEMPDIRECTORY/openssl/
lipo -create $AGENT_TEMPDIRECTORY/openssl_i386/lib/libcrypto.a $AGENT_TEMPDIRECTORY/openssl_x86_64/lib/libcrypto.a -output $AGENT_TEMPDIRECTORY/openssl/lib/libcrypto.a
lipo -create $AGENT_TEMPDIRECTORYopenssl_i386/lib/libssl.a $AGENT_TEMPDIRECTORY/openssl_x86_64/lib/libssl.a -output $AGENT_TEMPDIRECTORY/openssl/lib/libssl.a
rm openssl-$OPENSSL_VERSION.tar.gz
