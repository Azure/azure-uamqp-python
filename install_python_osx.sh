#!/bin/bash

# Python 3.5 is only built for OSX 10.6+
PACKAGE_TYPE="macosx10.9"
if [[ "$PYTHONVERSION" =~ ^3.5 ]]; then
  PACKAGE_TYPE="macosx10.6"
fi

# Handle prerelease versions
PACKAGE_DIR="$PYTHONVERSION"
if [[ "$PYTHONVERSION" =~ ^([0-9.]+)[A-Za-z] ]]; then
  PACKAGE_DIR="${BASH_REMATCH[1]}"
fi

curl -sSO https://www.python.org/ftp/python/$PACKAGE_DIR/python-$PYTHONVERSION-$PACKAGE_TYPE.pkg
sudo installer -allowUntrusted -pkg python-$PYTHONVERSION-$PACKAGE_TYPE.pkg -target /
rm -f python-$PYTHONVERSION-$PACKAGE_TYPE.pkg
