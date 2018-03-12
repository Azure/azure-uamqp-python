uAMQP for Python
================

An AMQP 1.0 client library for Python.


Installation
============

Wheels are provided for all major operating systems, so you can install directly with pip:

.. code:: shell

    $ pip install uamqp


If you are running a Linux distro that does not support `ManyLinux1 <https://www.python.org/dev/peps/pep-0513>`__, you can install from source:

.. code:: shell

    $ apt-get update
    $ apt-get install -y build-essential libssl-dev python3-dev uuid-dev cmake python3-pip
    $ pip3 install uamqp --no-binary


Python 2.7 support
++++++++++++++++++
Coming soon...


Developer Setup
===============
In order to run the code directly, the Cython extension will need to be build first.

Pre-requisites
++++++++++++++

- Windows: None
- Linux: Install dependencies as descriped above in the installation instructions.
- MacOS: Install OpenSSL and UUID using Homebrew:

.. code:: shell

    $ brew install openssl@1.1
    $ brew install ossp-uuid

Building the extension
++++++++++++++++++++++

This project has two C library dependencies:

- `Azure uAMQP for C <https://github.com/Azure/azure-uamqp-c>`__
- `Azure Shared Utility <https://github.com/Azure/azure-c-shared-utility>`__

They are vendored in this repository in these versions:
- Azure uAMQP @1.2.0
- Azure C Shared Utility @2018-03-07-temp-pod

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
