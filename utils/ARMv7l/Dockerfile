FROM resin/raspberrypi3-debian:wheezy

RUN apt-get update && \
    apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev unzip && \
    apt-get install -y libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev wget && \
    apt-get install -y libexpat1-dev liblzma-dev zlib1g-dev cmake curl libffi-dev tk-dev libc6-dev
# TODO:  patchelf

# Build OpenSSL 1.0.2g
ENV OPENSSL_VERSION 1.0.2g
RUN curl -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz && \
    tar -xvzf openssl-$OPENSSL_VERSION.tar.gz && \
    mv openssl-$OPENSSL_VERSION openssl_armv7l_src && \
    cd openssl_armv7l_src && \
    ./Configure linux-armv4 no-shared -static --openssldir=/opt/uamqp/openssl --prefix=/opt/uamqp/openssl && \
    make && \
    make install

# Build Python 3.4
RUN curl -O https://www.python.org/ftp/python/3.4.1/Python-3.4.1.tar.xz && \
    tar xf Python-3.4.1.tar.xz && \
    cd Python-3.4.1 && \
    ./configure && \
    make && \
    sudo make altinstall

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
RUN apt-get install -y libffi-dev tk-dev libc6-dev
RUN curl -O https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tar.xz && \
    tar xf Python-3.7.0.tar.xz && \
    cd Python-3.7.0 && \
    ./configure && \
    make && \
    sudo make altinstall

# Install setup for Python 3.4
RUN wget https://github.com/pypa/setuptools/archive/v40.0.0.tar.gz && \
    tar xf v40.0.0.tar.gz && \
    cd setuptools-40.0.0 && \
    python3.4 bootstrap.py && \
    python3.4 setup.py install
RUN wget https://files.pythonhosted.org/packages/21/89/ca320e5b45d381ae0df74c4b5694f1471c1b2453c5eb4bac3449f5970481/Cython-0.28.5.tar.gz#sha256=b64575241f64f6ec005a4d4137339fb0ba5e156e826db2fdb5f458060d9979e0 && \
    tar xf Cython-0.28.5.tar.gz && \
    cd Cython-0.28.5 && \
    python3.4 setup.py install
RUN wget https://files.pythonhosted.org/packages/2a/fb/aefe5d5dbc3f4fe1e815bcdb05cbaab19744d201bbc9b59cfa06ec7fc789/wheel-0.31.1.tar.gz#sha256=0a2e54558a0628f2145d2fc822137e322412115173e8a2ddbe1c9024338ae83c && \
    tar xf wheel-0.31.1.tar.gz && \
    cd wheel-0.31.1 && \
    python3.4 setup.py install
RUN wget https://files.pythonhosted.org/packages/cf/f7/21e21195874e85718ae2826774023a4601170199ebb32db451e447d19d91/auditwheel-1.9.0.tar.gz#sha256=fe8cbf74d16e7d1a89fd96b689f8e16f196edfb66cc98eb8a345bc03e28fed63 && \
    tar xf auditwheel-1.9.0.tar.gz && \
    cd auditwheel-1.9.0 && \
    python3.4 setup.py install

# Install setup for Python 3.5, 3.6, 3.7
RUN pip3.5 install cython wheel auditwheel
RUN pip3.6 install cython wheel auditwheel
#RUN pip3.7 install cython wheel auditwheel

# Build cmake 2.8.11
RUN curl -O https://cmake.org/files/v2.8/cmake-2.8.11.tar.gz && \
    tar xvf cmake-2.8.11.tar.gz && \
    cd cmake-2.8.11 && \
    ./bootstrap && \
    make && \
    make install

ENTRYPOINT /bin/bash