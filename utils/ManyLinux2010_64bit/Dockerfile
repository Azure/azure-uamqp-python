FROM ghcr.io/pyca/cryptography-manylinux2010:x86_64

# Build cmake 3.11
RUN pushd /tmp && \
    curl -O https://cmake.org/files/v3.11/cmake-3.11.0.tar.gz && \
    tar xvf cmake-3.11.0.tar.gz && \
    cd cmake-3.11.0 && \
    ./bootstrap && \
    make && \
    make install && \
    popd

# Build libuuid
RUN pushd /tmp && \
    curl -O https://cdn.kernel.org/pub/linux/utils/util-linux/v2.27/util-linux-2.27.1.tar.gz && \
    tar xvf util-linux-2.27.1.tar.gz && \
    cd util-linux-2.27.1 && \
    ./configure --disable-shared --disable-all-programs --enable-libuuid CFLAGS=-fPIC && \
    make && \
    make install && \
    popd
