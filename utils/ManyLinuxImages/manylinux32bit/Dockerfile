FROM quay.io/pypa/manylinux1_i686

ENV MANY_LINUX_IMAGE True
ENV CFLAGS -fPIC
ENV CWD $(pwd)

ARG OPENSSL_VERSION="1.1.0g"
ARG UUID_VERSION="2.31"

# Install new Perl because OpenSSL configure scripts require > 5.10.0.
ENV PERLBREW_ROOT /root/perl5/perlbrew
RUN curl -L https://install.perlbrew.pl | bash && \
    source $PERLBREW_ROOT/etc/bashrc && \
    perlbrew install perl-5.16.0 && \
    perlbrew use perl-5.16.0
    
# Install Python packaging dependencies
RUN /opt/python/cp34-cp34m/bin/pip install -U setuptools wheel pip cython && \
    /opt/python/cp35-cp35m/bin/pip install -U setuptools wheel pip cython && \
    /opt/python/cp36-cp36m/bin/pip install -U setuptools wheel pip cython

# Build and install OpenSSL
#RUN source $PERLBREW_ROOT/etc/bashrc && \
#    perlbrew use perl-5.16.0 && \
#    curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz && \
#    tar xvf openssl-$OPENSSL_VERSION.tar.gz && \
#    cd openssl-$OPENSSL_VERSION && \
#    ./config no-shared no-ssl2 no-ssl3 -fPIC --prefix=/openssl && \
#    make && make install && \
#    cd ..
    
# Build and install UUID
RUN curl -O https://www.kernel.org/pub/linux/utils/util-linux/v$UUID_VERSION/util-linux-$UUID_VERSION.tar.gz && \
    mkdir util-linux && tar xfv util-linux-$UUID_VERSION.tar.gz -C util-linux --strip-components 1 && \
    cd util-linux && \
    ./configure --prefix=/linux-util --disable-all-programs --enable-libuuid --enable-shared && \
    make && make install && \
    mkdir libuuid/src/uuid && cp libuuid/src/uuid.h libuuid/src/uuid/uuid.h && \
    cd ..
    