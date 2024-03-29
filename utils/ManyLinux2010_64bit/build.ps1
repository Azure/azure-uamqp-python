param (
    [string]
    $TAG
)

az acr login --subscription "Azure SDK Engineering System" --name azuresdkimages
az acr build --subscription "Azure SDK Engineering System" -r azuresdkimages -t azuresdkimages.azurecr.io/manylinux2010_crypto_x64:$TAG .
docker pull azuresdkimages.azurecr.io/manylinux2010_crypto_x64:$TAG
docker tag azuresdkimages.azurecr.io/manylinux2010_crypto_x64:$TAG azuresdkimages.azurecr.io/manylinux2010_crypto_x64:latest
docker push azuresdkimages.azurecr.io/manylinux2010_crypto_x64:latest
