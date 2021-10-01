FROM azuresdkimages.azurecr.io/manylinux_crypto_x64:3.9

# download source
RUN yum install gcc openssl-devel bzip2-devel libffi libffi-dev libffi-devel -y \
    && curl -O https://www.python.org/ftp/python/3.10.0/Python-3.10.0rc2.tgz \
    && tar -xzf ./Python-3.10.0rc2.tgz

# copy file with necessary configurations for openssl
COPY Setup /root/Python-3.10.0rc2/Modules/Setup

ENV CFLAGS=-I/usr/lib64/libffi-3.0.5/include

# ensure none of the lineendings in the copied file were wrong. install python3.10
RUN ldconfig \
    && sed -i -e 's/\r$//' /root/Python-3.10.0rc2/Modules/Setup \
    && cd Python-3.10.0rc2 \
    && ./configure --enable-optimizations \
    && make altinstall

# ensure proper symlinks are in place as necessary for tooling
RUN mkdir -p /opt/python/cp310-cp310/bin \
    && ln -s /usr/local/bin/python3.10 /opt/python/cp310-cp310/bin/python \
    && ln -s /usr/local/bin/pip3.10 /opt/python/cp310-cp310/bin/pip
