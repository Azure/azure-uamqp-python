#!/bin/bash

# Python 3.8+ are only build for OSX 10.9+
PACKAGE_TYPE="macosx10.6"
if [[ "$PYTHONVERSION" =~ ^3.8 ]]; then
  PACKAGE_TYPE="macosx10.9"
fi

# Handle prerelease versions
PACKAGE_DIR="$PYTHONVERSION"
if [[ "$PYTHONVERSION" =~ ^([0-9.]+)[A-Za-z] ]]; then
  PACKAGE_DIR="${BASH_REMATCH[1]}"
fi

curl -sSO https://www.python.org/ftp/python/$PACKAGE_DIR/python-$PYTHONVERSION-$PACKAGE_TYPE.pkg
sudo installer -allowUntrusted -pkg python-$PYTHONVERSION-$PACKAGE_TYPE.pkg -target /
rm -f python-$PYTHONVERSION-$PACKAGE_TYPE.pkg

echo "##vso[task.prependpath]/usr/local/bin"