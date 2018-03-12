#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import sys
import re
import distutils
from setuptools import find_packages, setup
from distutils.extension import Extension

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

supress_link_flags = os.environ.get("UAMQP_SUPPRESS_LINK_FLAGS", False)
is_win = sys.platform.startswith('win')
is_mac = sys.platform.startswith('darwin')

# Version extraction inspired from 'requests'
with open(os.path.join('uamqp', '__init__.py'), 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


cwd = os.path.abspath('.')

# Headers

pxd_inc_dir = os.path.join(cwd, "src", "vendor", "inc")
sys.path.insert(0, pxd_inc_dir)

include_dirs = [
    pxd_inc_dir,
    # azure-c-shared-utility inc
    "./src/vendor/azure-c-shared-utility/pal/inc",
    "./src/vendor/azure-c-shared-utility/inc",
    "./src/vendor/azure-c-shared-utility/pal/windows" if is_win else "./src/vendor/azure-c-shared-utility/pal/linux",
    # azure-uamqp-c inc
    "./src/vendor/azure-uamqp-c/inc",
]

# Build unique source pyx

c_uamqp_src = None
if USE_CYTHON:
    content_includes = ""
    for f in os.listdir("./src"):
        if is_win and 'openssl' in f:
            continue
        elif not is_win and 'schannel' in f:
            continue
        if f.endswith(".pyx"):
            print("Adding {}".format(f))
            content_includes += "include \"src/" + f + "\"\n"
    c_uamqp_src = os.path.join("uamqp", "c_uamqp.pyx")
    with open(c_uamqp_src, 'w') as lib_file:
        lib_file.write(content_includes)
else:
    c_uamqp_src = "uamqp/c_uamqp.c"


# Libraries and extra compile args

kwargs = {}
if is_win:
    kwargs['extra_compile_args'] = ['/openmp']
    kwargs['libraries'] = [
        'AdvAPI32',
        'Crypt32',
        'ncrypt',
        'Secur32',
        'schannel',
        'RpcRT4',
        'WSock32',
        'WS2_32']
else:
    kwargs['extra_compile_args'] = ['-g', '-O0', "-std=gnu99", "-fPIC"]
    # SSL before crypto matters: https://bugreports.qt.io/browse/QTBUG-62692
    if not supress_link_flags:
        kwargs['libraries'] = ['ssl', 'crypto', 'uuid']

# Sources

sources = [
    "./src/vendor/azure-c-shared-utility/src/xlogging.c",
    "./src/vendor/azure-c-shared-utility/src/optionhandler.c",
    "./src/vendor/azure-c-shared-utility/src/consolelogger.c",
    "./src/vendor/azure-c-shared-utility/src/gballoc.c",
    "./src/vendor/azure-c-shared-utility/src/vector.c",
    "./src/vendor/azure-c-shared-utility/src/crt_abstractions.c",
    "./src/vendor/azure-c-shared-utility/src/uuid.c",
    "./src/vendor/azure-c-shared-utility/src/xio.c",
    "./src/vendor/azure-c-shared-utility/src/strings.c",
    "./src/vendor/azure-c-shared-utility/src/string_tokenizer.c",
    "./src/vendor/azure-c-shared-utility/src/doublylinkedlist.c",
    "./src/vendor/azure-c-shared-utility/src/map.c",
    "./src/vendor/azure-c-shared-utility/src/sastoken.c",
    "./src/vendor/azure-c-shared-utility/src/urlencode.c",
    "./src/vendor/azure-c-shared-utility/src/hmacsha256.c",
    "./src/vendor/azure-c-shared-utility/src/base64.c",
    "./src/vendor/azure-c-shared-utility/src/buffer.c",
    "./src/vendor/azure-c-shared-utility/src/hmac.c",
    "./src/vendor/azure-c-shared-utility/src/usha.c",
    "./src/vendor/azure-c-shared-utility/src/sha1.c",
    "./src/vendor/azure-c-shared-utility/src/sha224.c",
    "./src/vendor/azure-c-shared-utility/src/sha384-512.c",
    "./src/vendor/azure-c-shared-utility/src/singlylinkedlist.c",
    "./src/vendor/azure-c-shared-utility/src/connection_string_parser.c",
    "./src/vendor/azure-c-shared-utility/adapters/agenttime.c",
    "./src/vendor/azure-c-shared-utility/src/tlsio_schannel.c" if is_win else "./src/vendor/azure-c-shared-utility/src/tlsio_openssl.c",
    "./src/vendor/azure-c-shared-utility/adapters/platform_win32.c" if is_win else "./src/vendor/azure-c-shared-utility/adapters/platform_linux.c",
    "./src/vendor/azure-c-shared-utility/adapters/tickcounter_win32.c" if is_win else "./src/vendor/azure-c-shared-utility/adapters/tickcounter_linux.c",
    "./src/vendor/azure-c-shared-utility/adapters/socketio_win32.c" if is_win else "./src/vendor/azure-c-shared-utility/adapters/socketio_berkeley.c",
    "./src/vendor/azure-c-shared-utility/adapters/uniqueid_win32.c" if is_win else "./src/vendor/azure-c-shared-utility/adapters/uniqueid_linux.c",
    "./src/vendor/azure-c-shared-utility/adapters/lock_win32.c" if is_win else "./src/vendor/azure-c-shared-utility/adapters/lock_pthreads.c",
    "./src/vendor/azure-c-shared-utility/adapters/threadapi_win32.c" if is_win else "./src/vendor/azure-c-shared-utility/adapters/threadapi_pthreads.c",
    "./src/vendor/azure-c-shared-utility/adapters/condition_win32.c" if is_win else "./src/vendor/azure-c-shared-utility/adapters/condition_pthreads.c",
    "./src/vendor/azure-uamqp-c/src/amqpvalue.c",
    "./src/vendor/azure-uamqp-c/src/amqp_management.c",
    "./src/vendor/azure-uamqp-c/src/frame_codec.c",
    "./src/vendor/azure-uamqp-c/src/amqp_frame_codec.c",
    "./src/vendor/azure-uamqp-c/src/sasl_frame_codec.c",
    "./src/vendor/azure-uamqp-c/src/link.c",
    "./src/vendor/azure-uamqp-c/src/cbs.c",
    "./src/vendor/azure-uamqp-c/src/connection.c",
    "./src/vendor/azure-uamqp-c/src/async_operation.c",
    "./src/vendor/azure-uamqp-c/src/message.c",
    "./src/vendor/azure-uamqp-c/src/messaging.c",
    "./src/vendor/azure-uamqp-c/src/message_sender.c",
    "./src/vendor/azure-uamqp-c/src/message_receiver.c",
    "./src/vendor/azure-uamqp-c/src/amqp_definitions.c",
    "./src/vendor/azure-uamqp-c/src/amqpvalue_to_string.c",
    "./src/vendor/azure-uamqp-c/src/sasl_mechanism.c",
    "./src/vendor/azure-uamqp-c/src/sasl_server_mechanism.c",
    "./src/vendor/azure-uamqp-c/src/sasl_mssbcbs.c",
    "./src/vendor/azure-uamqp-c/src/sasl_plain.c",
    "./src/vendor/azure-uamqp-c/src/saslclientio.c",
    "./src/vendor/azure-uamqp-c/src/sasl_anonymous.c",
    "./src/vendor/azure-uamqp-c/src/session.c",
    "./src/vendor/azure-uamqp-c/src/socket_listener_win32.c" if is_win else "./src/vendor/azure-uamqp-c/src/socket_listener_berkeley.c",
    c_uamqp_src,
]

if is_win:
    sources.extend([
        "./src/vendor/azure-c-shared-utility/adapters/socketio_win32.c",
        "./src/vendor/azure-c-shared-utility/src/x509_schannel.c",
    ])
else:
    sources.extend([
        "./src/vendor/azure-c-shared-utility/adapters/linux_time.c",
        "./src/vendor/azure-c-shared-utility/src/x509_openssl.c",
    ])

# Configure the extension

extensions = [Extension(
        "uamqp.c_uamqp",
        sources=sources,
        include_dirs=include_dirs,
        **kwargs)
    ]

with open('README.rst', encoding='utf-8') as f:
    readme = f.read()
with open('HISTORY.rst', encoding='utf-8') as f:
    history = f.read()

if USE_CYTHON:
    extensions = cythonize(extensions)

setup(
    name='uamqp',
    version=version,
    description='AMQP 1.0 Client Library for Python',
    long_description=readme + '\n\n' + history,
    license='MIT License',
    author='Microsoft Corporation',
    author_email='azpysdkhelp@microsoft.com',
    url='https://github.com/Azure/azure-uamqp-python',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Cython',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
    ],
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=["tests"]),
    ext_modules = extensions
)
