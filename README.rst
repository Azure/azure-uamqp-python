uAMQP for Python
================

An AMQP 1.0 client library for Python.


Installation
============

Windows and MacOS
+++++++++++++++++

Wheels are provided for these platforms, so you can install directly with pip:

.. code:: shell

    $ pip install uamqp


Linux
+++++

On Linux you must install the dependencies before you install from pip, like so:

.. code:: shell

    $ apt-get update
    $ apt-get install build-essential libssl-dev python3-dev uuid-dev
    $ pip3 install uamqp --no-binary

Or for RHEL/CentOS:

.. code:: shell

    $ yum install redhat-rpm-config gcc openssl-devel python-devel libuuid-devel

Python 2.7 support
++++++++++++++++++
Coming soon...


Developer Setup
===============
In order to run the code directly, the Cython extension will need to be build first.

Pre-requisites
++++++++++++++

- Windows: None
- MacOS: Install OpenSSL using Homebrew: `brew install openssl@1.1`
- Linux: Install dependencies as descriped above in the installation instructions.

Building the extension
++++++++++++++++++++++

This project has two C library dependencies:

- `Azure uAMQP for C <https://github.com/Azure/azure-uamqp-c>`__
- `Azure Shared Utility <https://github.com/Azure/azure-c-shared-utility>`__

In order to build the Python extension, both of these repos will need to be cloned into the root directory.
To build, start by creating a virtual environment and installing the required Python packages:

.. code:: shell

    $ python -m venv env
    $ env/Scripts/activate
    (env)$ pip install -r requirements.txt

Next, run the build command:

.. code:: shell

    $ python setup.py built_ext --inplace

Tests
+++++

The tests can be run from within the virtual environment. The extension must be built first using the instructions above.

.. code:: shell

    (env)$ pytest


Provide Feedback
================

If you encounter any bugs or have suggestions, please file an issue in the
`Issues <https://github.com/Azure/azure-uamqp-python/issues>`__
section of the project.


Contributing
============

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
