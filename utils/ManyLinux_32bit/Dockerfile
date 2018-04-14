FROM quay.io/pypa/manylinux1_i686 

# Install new Perl because OpenSSL configure scripts require > 5.10.0.
ENV PERLBREW_ROOT /root/perl5/perlbrew
RUN curl -L https://install.perlbrew.pl | bash && \
    source $PERLBREW_ROOT/etc/bashrc && \
    perlbrew install perl-5.16.0 && \
    perlbrew use perl-5.16.0

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

ARG OPENSSL_VERSION="1.0.2n"

# Build OpenSSL
RUN source $PERLBREW_ROOT/etc/bashrc && \
    perlbrew use perl-5.16.0 && \
    pushd /tmp && \
    curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz && \
    tar xvf openssl-$OPENSSL_VERSION.tar.gz
   #cd openssl-$OPENSSL_VERSION && \
    #./config shared no-zlib no-ssl2
    #make depend
#RUN pushd /tmp && \
#    cd openssl-$OPENSSL_VERSION && \
#    ./config shared no-zlib no-ssl2

#RUN make depend
    #make && \
    #make install && \
    #popd && \