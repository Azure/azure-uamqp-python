# step 1: install requirements for building pyca manylinux1_x86_64
# copied from https://github.com/pyca/infra/tree/147cd4e521a2cfac822d7902471de9408958cd31
FROM quay.io/pypa/manylinux1_x86_64
MAINTAINER Python Cryptographic Authority
WORKDIR /root
RUN yum -y install prelink && yum -y clean all
RUN curl -O https://www.cpan.org/src/5.0/perl-5.24.1.tar.gz
RUN tar zxf perl-5.24.1.tar.gz && \
    cd perl-5.24.1 && \
    ./Configure -des -Dprefix=/opt/perl && \
    make -j4 && make install
ADD install_libffi.sh /root/install_libffi.sh
RUN sh install_libffi.sh manylinux1
ADD install_openssl.sh /root/install_openssl.sh
ADD openssl-version.sh /root/openssl-version.sh
RUN sh install_openssl.sh manylinux1
ADD install_virtualenv.sh /root/install_virtualenv.sh
RUN sh install_virtualenv.sh manylinux1

# step2: install requirements for building uamqp

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
