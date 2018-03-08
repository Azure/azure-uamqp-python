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
from Cython.Build import cythonize
from distutils.extension import Extension
from Cython.Distutils import build_ext
from wheel.bdist_wheel import bdist_wheel


is_win = sys.platform.startswith('win')
is_mac = sys.platform.startswith('darwin')
is_manylinux = os.environ.get('MANY_LINUX_IMAGE', False)

# Version extraction inspired from 'requests'
with open(os.path.join('uamqp', 'version.py'), 'r') as fd:
    version = re.search(r'^VERSION\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


cwd = os.path.abspath('.')
pxd_inc_dir = os.path.join(cwd, "src", "vendor", "inc")
sys.path.insert(0, pxd_inc_dir)

dirs = [
    pxd_inc_dir,
    "/usr/local/include/openssl",
    "/usr/local/opt/openssl/include",
    "/usr/include",
    "/util-linux/libuuid/src",
    "/openssl/include",
    # azure-c-shared-utility inc
    "./src/vendor/azure-c-shared-utility/pal/inc",
    "./src/vendor/azure-c-shared-utility/inc",
    # azure-uamqp-c inc
    "./src/vendor/azure-uamqp-c/inc"
]

default_ossl_base = '/usr/lib/x86_64-linux-gnu'
# Many Linux openssl install location
many_linux_ossl_base = '/openssl-src'
# Since openssl is deprecated on MacOSX 10.7+, look for homebrew installs
homebrew_ossl_base = '/usr/local/opt/openssl/lib'

def abs_ssl (path):
    if is_mac and os.path.exists(homebrew_ossl_base):
        return os.path.join(homebrew_ossl_base, path) + ".a"
    elif is_manylinux and os.path.exists(many_linux_ossl_base):
        return os.path.join(many_linux_ossl_base, path) + ".a"
    else:
        return os.path.join(default_ossl_base, path) + ".so"


if is_win:
    dirs.extend([
        "./src/vendor/azure-c-shared-utility/pal/windows",
    ])
else:
    dirs.extend([
        "./src/vendor/azure-c-shared-utility/pal/linux",
    ])

content_includes = ""
for f in os.listdir("./src"):
    if is_win and 'openssl' in f:
        continue
    elif not is_win and 'schannel' in f:
        continue
    if f.endswith(".pyx"):
        print("Adding {}".format(f))
        content_includes += "include \"src/" + f + "\"\n"
combined_pyx = os.path.join("uamqp", "c_uamqp.pyx")
with open(combined_pyx, 'w') as lib_file:
    lib_file.write(content_includes)

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
    if not is_mac and not is_manylinux:
        kwargs['libraries'] = ['uuid']
    kwargs['extra_link_args'] = [abs_ssl('libcrypto'), abs_ssl('libssl')]
    kwargs['extra_compile_args'] = ['-g', '-O0', "-std=gnu99", "-fPIC"]
    if is_manylinux:
        kwargs['extra_link_args'].insert(0, '/util-linux/.libs/libuuid.a')

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
    "./src/vendor/azure-uamqp-c/src/socket_listener_win32.c" if is_win  else "./src/vendor/azure-uamqp-c/src/socket_listener_berkeley.c",
    combined_pyx,
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

extensions = [Extension(
        "uamqp.c_uamqp",
        sources=sources,
        include_dirs=dirs,
        **kwargs)
    ]

with open('README.rst', encoding='utf-8') as f:
    readme = f.read()
with open('HISTORY.rst', encoding='utf-8') as f:
    history = f.read()

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
    cmdclass = {'build_ext': build_ext, 'bdist_wheel': bdist_wheel},
    ext_modules = cythonize(extensions, gdb_debug=True)
)