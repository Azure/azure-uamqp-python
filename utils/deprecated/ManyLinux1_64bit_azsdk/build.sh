#!/bin/sh
[ -z "$TAG" ] && echo "Must set \$TAG to a value (e.g. '3.8')" && exit 1

az acr login --subscription "Azure SDK Engineering System" --name azuresdkimages || exit 1
az acr build --subscription "Azure SDK Engineering System" -r azuresdkimages -t azuresdkimages.azurecr.io/manylinux_crypto_x64_azsdk:$TAG .
docker pull azuresdkimages.azurecr.io/manylinux_crypto_x64_azsdk:$TAG
docker tag azuresdkimages.azurecr.io/manylinux_crypto_x64_azsdk:$TAG azuresdkimages.azurecr.io/manylinux_crypto_x64_azsdk:latest
docker push azuresdkimages.azurecr.io/manylinux_crypto_x64_azsdk:latest
