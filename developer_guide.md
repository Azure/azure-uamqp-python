# uAMQP Developer Guide

This guide will help you understand how to develop uAMQP locally as well as update the various components of the library. The library is no longer in active development, but is still updated for security and critical bug fixes. No new feature development or future releases are planned. 


## Components

The project has two C library dependencies, they are vendored in the repository and the last update was in Sept 2024:
* [Azure uAMQP for C](https://github.com/Azure/azure-uamqp-c) - Last vendor [commit](https://github.com/Azure/azure-uamqp-c/commit/96d7179f60e558b2c350194ea0061c725377f7e0) 
* [Azure C Shared Utility](https://github.com/Azure/azure-c-shared-utility) - Last vendor [commit](https://github.com/Azure/azure-c-shared-utility/commit/51d6f3f7246876051f713c7abed28f909bf604e3)

These libraries are updated whenever there is a security or critical bug fix that needs to be applied. The process is to update the vendored libraries manually by copying the files over into the vendor directory. 

## Setting up the development environment

### Pre-requisites for building the library:
* Python 3.9 or later
* Visual Studio 2022 or later (Windows)
* Docker (Linux and Windows)

The library is built using [cibuildwheel ](https://cibuildwheel.pypa.io/en/stable/) which helps you build wheels across Windows, Linux and macOS. This is the same library that is used to build the wheels for the Python Package Index (PyPI). This library will download the necessary docker images for the platforms you are building for and build the wheels in a consistent manner across all platforms.

* Create a virtual environment and install the required dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r dev_requirements.txt
```

* Build the library using cibuildwheel:

```bash
cibuildwheel --platform linux
cibuildwheel --platform windows
```

The built wheels will be placed in the `wheelhouse` directory. You can then install the built wheel using pip and test changes:

```bash
pip install wheelhouse/your_wheel_file.whl
```

To change the build configuration, for example to set minimum python to build wheels for, pass in compilation flags etc the `pyproject.toml` file can be modified. For further details and configuration options refer to the [cibuildwheel documentation](https://cibuildwheel.pypa.io/en/stable/configuration/).

After these changes are validated and tested locally, they need to be applied to the [client.test.live.yml](.azure-pipelines/client.test.live.yml) and [client.test.yml](.azure-pipelines/client.test.yml) files to ensure that the changes are applied to the CI/CD pipeline. The pipeline will then build the library and run the tests on the changes made.

### Update OpenSSL version

The library is compiled using the latest OpenSSL LTS version update available. The [install_openssl.sh](scripts/install_openssl.sh) script is used to download and compile the OpenSSL library. This script is run as part of the build process in the CI/CD pipeline and locally by cibuildwheel. To update the version, make the necessary changes in this file and commit the changes.

### Testing the library

The [all tests pipeline](https://dev.azure.com/azure-sdk/internal/_build?definitionId=307&_a=summary) runs all the tests in the library across Linux, Windows, macOS for python 3.9 and later. The tests are run using the [pytest](https://docs.pytest.org/en/stable/) framework. This is used to validate that wheels are built correctly and that the library works as expected.

### Releasing the library

To release a new version of the library, the following steps are needed:
* Update the version in [__init__.py](uamqp/__init__.py) file
* Update the [History](HISTORY.md) file with the changes made in the release
* Release using the [client pipeline](https://dev.azure.com/azure-sdk/internal/_build?definitionId=88&_a=summary) which will build the library and publish it to PyPI
