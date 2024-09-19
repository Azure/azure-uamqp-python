#!/bin/bash
set -xe

OPENSSL_URL="https://github.com/openssl/openssl/releases/download/"

export OPENSSL_VERSION="openssl-3.2.3"
export OPENSSL_SHA256=" 52b5f1c6b8022bc5868c308c54fb77705e702d6c6f4594f99a0df216acf46239"
# We need a base set of flags because on Windows using MSVC
# enable-ec_nistp_64_gcc_128 doesn't work since there's no 128-bit type
export OPENSSL_BUILD_FLAGS_WINDOWS="no-ssl3 no-ssl3-method no-zlib no-shared no-comp no-dynamic-engine"
export OPENSSL_BUILD_FLAGS="${OPENSSL_BUILD_FLAGS_WINDOWS} enable-ec_nistp_64_gcc_128"

function check_sha256sum {
    local fname=$1
    local sha256=$2
    echo "${sha256}  ${fname}" > "${fname}.sha256"
    sha256sum -c "${fname}.sha256"
    rm "${fname}.sha256"
}

curl -#LO "${OPENSSL_URL}/${OPENSSL_VERSION}/${OPENSSL_VERSION}.tar.gz"
check_sha256sum ${OPENSSL_VERSION}.tar.gz ${OPENSSL_SHA256}
tar zxf ${OPENSSL_VERSION}.tar.gz
PATH=/opt/perl/bin:$PATH
pushd ${OPENSSL_VERSION}
./config $OPENSSL_BUILD_FLAGS --prefix=/opt/pyca/cryptography/openssl --openssldir=/opt/pyca/cryptography/openssl
make depend
make -j4
# avoid installing the docs
# https://github.com/openssl/openssl/issues/6685#issuecomment-403838728
make install_sw install_ssldirs
popd
rm -rf openssl*