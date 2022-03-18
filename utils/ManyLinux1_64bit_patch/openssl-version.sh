export OPENSSL_VERSION="openssl-1.1.1n"
export OPENSSL_SHA256="40dceb51a4f6a5275bde0e6bf20ef4b91bfc32ed57c0552e2e8e15463372b17a"
# We need a base set of flags because on Windows using MSVC
# enable-ec_nistp_64_gcc_128 doesn't work since there's no 128-bit type
export OPENSSL_BUILD_FLAGS_WINDOWS="no-ssl3 no-ssl3-method no-zlib no-shared no-comp no-dynamic-engine"
export OPENSSL_BUILD_FLAGS="${OPENSSL_BUILD_FLAGS_WINDOWS} enable-ec_nistp_64_gcc_128"