FROM resin/raspberrypi3-debian:stretch

RUN apt-get update && \
    apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev && \
    apt-get install -y libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev  && \
    apt-get install -y libexpat1-dev liblzma-dev zlib1g-dev cmake curl libffi-dev tk-dev libc6-dev

# Build Python 3.5
RUN curl -O https://www.python.org/ftp/python/3.5.5/Python-3.5.5.tar.xz && \
    tar xf Python-3.5.5.tar.xz && \
    cd Python-3.5.5 && \
    ./configure && \
    make && \
    sudo make altinstall

# Build Python 3.6
RUN curl -O https://www.python.org/ftp/python/3.6.6/Python-3.6.6.tar.xz && \
    tar xf Python-3.6.6.tar.xz && \
    cd Python-3.6.6 && \
    ./configure && \
    make && \
    sudo make altinstall

# Build Python 3.7
RUN apt install -y libffi-dev tk-dev libc6-dev
RUN curl -O https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tar.xz && \
    tar xf Python-3.7.0.tar.xz && \
    cd Python-3.7.0 && \
    ./configure && \
    make && \
    sudo make altinstall

# Build Python 3.4
RUN curl -O https://www.python.org/ftp/python/3.4.1/Python-3.4.1.tar.xz && \
    tar xf Python-3.4.1.tar.xz && \
    cd Python-3.4.1 && \
    ./configure && \
    make && \
    sudo make altinstall

# Build OpenSSL 1.0.2g
#ENV OPENSSL_VERSION 1.0.2o
#RUN curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz && \
#    tar -xvzf openssl-$OPENSSL_VERSION.tar.gz && \
#    mv openssl-$OPENSSL_VERSION openssl_armv7l_src && \
#    cd openssl_armv7l_src && \
#    ./Configure linux-armv4 shared --openssldir=/etc/ssl --prefix=/opt/uamqp/openssl && \
#    make && \
#    make install && \
#    rm openssl-$OPENSSL_VERSION.tar.gz

ENTRYPOINT /bin/bash