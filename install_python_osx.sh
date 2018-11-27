#!/bin/bash

curl -O https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-macosx10.6.pkg
sudo installer -allowUntrusted -pkg python-$PYTHON_VERSION-macosx10.6.pkg -target /
rm -f python-$PYTHON_VERSION-macosx10.6.pkg
