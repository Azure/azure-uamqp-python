FROM azuresdkimages.azurecr.io/manylinux_crypto_x64:latest

WORKDIR /root

COPY ./openssl-version.sh /root/openssl-version.sh
RUN sh /root/install_openssl.sh