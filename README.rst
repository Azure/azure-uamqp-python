uAMQP for Python
================
.. image:: https://img.shields.io/pypi/v/uamqp.svg
    :target: https://pypi.python.org/pypi/uamqp/

.. image:: https://img.shields.io/pypi/pyversions/uamqp.svg
    :target: https://pypi.python.org/pypi/uamqp/

.. image:: https://dev.azure.com/azure-sdk/public/_apis/build/status/python/azure-uamqp-python%20-%20client?branchName=main
    :target: https://dev.azure.com/azure-sdk/public/_build?definitionId=89

An AMQP 1.0 client library for Python.

Disclaimer
============

This repo is no longer in active maintenance and we plan on deprecating it sometime in the first quarter of 2025. The EventHubs & Service Bus client libraries are now using the 
python based AMQP library which is under active development. If there is interest in using the new python library as standalone, please share your interest in this `issue <https://github.com/Azure/azure-uamqp-python/issues/374>`__.

uAMQP for Python requires Python 3.6+ starting from v1.5, and Python 2.7 is no longer supported. If Python 2.7 is required, please install uAMQP v1.4.3:

.. code:: shell

    $ pip install uamqp==1.4.3

Installation
============

Wheels are provided for most major operating systems, so you can install directly with pip:

.. code:: shell

    $ pip install uamqp


If you are running a Linux distro that does not support `ManyLinux1 <https://www.python.org/dev/peps/pep-0513>`__ or you need to customize the build based on your system settings and packages, you can install from source:

.. code:: shell

    $ apt-get update
    $ apt-get install -y build-essential libssl-dev uuid-dev cmake libcurl4-openssl-dev pkg-config python3-dev python3-pip
    $ pip3 install uamqp --no-binary :all:

If you are running Alpine, you can install from source:

.. code:: shell

    $ apk add --update python3 py-pip python3-dev cmake gcc g++ openssl-dev build-base
    $ pip3 install uamqp --no-binary :all:

If you are running Red Hat, you can install from source:

.. code:: shell

    $ yum install cmake gcc gcc-c++ make openssl-devel python3-devel
    $ pip3 install uamqp --no-binary :all:


Documentation
+++++++++++++
Reference documentation can be found here: `docs.microsoft.com/python/api/uamqp/uamqp <https://docs.microsoft.com/python/api/uamqp/uamqp>`__.


Developer Setup
===============
In order to run the code directly, the Cython extension will need to be build first.

Pre-requisites
++++++++++++++

- Windows: Setup a `build environment <https://packaging.python.org/guides/packaging-binary-extensions/#building-binary-extensions>`__.
- Linux: Install dependencies as descriped above in the installation instructions.
- MacOS: Install cmake using Homebrew:

.. code:: shell

    $ brew install cmake

Building the extension
++++++++++++++++++++++

This project has two C library dependencies. They are vendored in this repository in these versions:

- `Azure uAMQP for C <https://github.com/Azure/azure-uamqp-c>`__ @ `2021-11-16 <https://github.com/Azure/azure-uamqp-c/tree/259db533a66a8fa6e9ac61c39a9dae880224145f>`__
- `Azure C Shared Utility <https://github.com/Azure/azure-c-shared-utility>`__ @ `2021-11-15 <https://github.com/Azure/azure-c-shared-utility/tree/735be16a943c2a9cbbddef0543f871f5bc0e27ab>`__

To build, start by creating a virtual environment and installing the required Python packages:

.. code:: shell

    $ python -m venv env
    $ env/Scripts/activate
    (env)$ pip install -r dev_requirements.txt

Next, run the build command:

.. code:: shell

    $ python setup.py build_ext --inplace

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
the rights to use your contribution. For details, visit `https://cla.microsoft.com <https://cla.microsoft.com>`__.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the `Microsoft Open Source Code of Conduct <https://opensource.microsoft.com/codeofconduct/>`__.
For more information see the `Code of Conduct FAQ <https://opensource.microsoft.com/codeofconduct/faq/>`__ or
contact `opencode@microsoft.com <mailto:opencode@microsoft.com>`__ with any additional questions or comments.
