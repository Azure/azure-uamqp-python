#!/bin/sh
[ -z "$TAG" ] && echo "Must set \$TAG to a value (e.g. '3.8')" && exit 1

az acr login --subscription "Azure SDK Engineering System" --name azuresdkimages || exit 1
az acr build --subscription "Azure SDK Engineering System" -r azuresdkimages -t azuresdkimages.azurecr.io/manylinux_crypto_x64:$TAG .
docker pull azuresdkimages.azurecr.io/manylinux_crypto_x64:$TAG
docker tag azuresdkimages.azurecr.io/manylinux_crypto_x64:$TAG azuresdkimages.azurecr.io/manylinux_crypto_x64:latest
docker push azuresdkimages.azurecr.io/manylinux_crypto_x64:latest
