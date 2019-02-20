#!/bin/bash

curl -O https://www.python.org/ftp/python/$PYTHONVERSION/python-$PYTHONVERSION-macosx10.6.pkg
sudo installer -allowUntrusted -pkg python-$PYTHONVERSION-macosx10.6.pkg -target /
rm -f python-$PYTHONVERSION-macosx10.6.pkg
