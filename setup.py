#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import os
import sys
import re
import distutils
import subprocess
import platform
from setuptools import find_packages, setup, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig
from distutils.extension import Extension
from distutils import log as logger

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

# If the C file doesn't exist and no Cython is available, die
if not os.path.exists("uamqp/c_uamqp.c") and not USE_CYTHON:
    raise ValueError("You need to install cython==0.27.3 in order to execute this setup.py if 'uamqp/c_uamqp.c' does not exists")

is_win = sys.platform.startswith('win')
is_mac = sys.platform.startswith('darwin')
use_openssl = os.environ.get('UAMQP_USE_OPENSSL', not (is_win or is_mac))
supress_link_flags = os.environ.get("UAMQP_SUPPRESS_LINK_FLAGS", False)

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
    "./src/vendor/azure-uamqp-c/deps/azure-c-shared-utility/pal/inc",
    "./src/vendor/azure-uamqp-c/deps/azure-c-shared-utility/inc",
    "./src/vendor/azure-uamqp-c/deps/azure-c-shared-utility/pal/windows" if is_win else "./src/vendor/azure-uamqp-c/deps/azure-c-shared-utility/pal/linux",
    # azure-uamqp-c inc
    "./src/vendor/azure-uamqp-c/inc",
]

# Build unique source pyx

def create_cython_file():
    content_includes = ""
    for f in os.listdir("./src"):
        if f.endswith(".pyx"):
            print("Adding {}".format(f))
            content_includes += "include \"src/" + f + "\"\n"
    c_uamqp_src = os.path.join("uamqp", "c_uamqp.pyx")
    with open(c_uamqp_src, 'w') as lib_file:
        lib_file.write(content_includes)
    return c_uamqp_src


def get_build_env():
    build_env = os.environ.copy()
    return build_env


def get_generator():
    if is_win and platform.architecture()[0] == '64bit':
        return "Visual Studio 14 2015 Win64"
    elif is_win:
        return "Visual Studio 14 2015"
    else:
        return "Unix Makefiles"



# Compile uamqp
# Inspired by https://stackoverflow.com/a/48015772/4074838

class UAMQPExtension(Extension):

    def __init__(self, name):
        # don't invoke the original build_ext for this special extension
        super(UAMQPExtension, self).__init__(name, sources=[])

def create_folder_no_exception(foldername):
    try:
        os.makedirs(foldername)
    except Exception: # Assume it's already there, and not impossible to create
        pass

class build_ext(build_ext_orig):

    def run(self):
        cmake_build_dir = None
        for ext in self.extensions:
            if isinstance(ext, UAMQPExtension):
                self.build_cmake(ext)
                # Now I have built in ext.cmake_build_dir
                cmake_build_dir = self.cmake_build_dir
            else:
                ext.library_dirs += [
                    cmake_build_dir,
                    cmake_build_dir + "/deps/azure-c-shared-utility/",
                    cmake_build_dir + "/Debug/",
                    cmake_build_dir + "/Release/",
                    cmake_build_dir + "/deps/azure-c-shared-utility/Debug/",
                    cmake_build_dir + "/deps/azure-c-shared-utility/Release/"
                ]
        super(build_ext, self).run()

    def build_cmake(self, ext):
        cwd = os.getcwd()

        # these dirs will be created in build_py, so if you don't have
        # any python sources to bundle, the dirs will be missing
        self.cmake_build_dir = self.build_temp + "/cmake"
        create_folder_no_exception(self.cmake_build_dir)

        extdir = self.get_ext_fullpath(ext.name)
        create_folder_no_exception(extdir)

        logger.info("will build uamqp in %s", self.cmake_build_dir)
        os.chdir(cwd + "/" + self.cmake_build_dir)

        generator = get_generator()
        logger.info("Building with generator: {}".format(generator))
        # Configure
        configure_command = [
            "cmake",
            cwd + "/src/vendor/azure-uamqp-c/",
            "-G \"{}\"".format(generator),
            "-Duse_openssl:bool={}".format("ON" if use_openssl else "OFF"),
            "-Duse_default_uuid:bool=ON ", # Should we use libuuid in the system or light one?
            "-Duse_builtin_httpapi:bool=ON ", # Should we use libcurl in the system or light one?
            "-Dskip_samples:bool=ON", # Don't compile uAMQP samples binaries
            "-DCMAKE_POSITION_INDEPENDENT_CODE=TRUE", # ask for -fPIC
            "-DCMAKE_BUILD_TYPE=Release"
        ]
        build_env = get_build_env()
        joined_cmd = " ".join(configure_command)
        logger.info("calling %s", joined_cmd)
        subprocess.check_call(joined_cmd, shell=True, universal_newlines=True, env=build_env)

        compile_command  = ["cmake", "--build", ".", "--config", "Release"]
        joined_cmd = " ".join(compile_command)
        logger.info("calling %s", joined_cmd)
        subprocess.check_call(joined_cmd, shell=True, universal_newlines=True, env=build_env)

        os.chdir(cwd)

        if USE_CYTHON:
            create_cython_file()

# Libraries and extra compile args

kwargs = {}
if is_win:
    kwargs['libraries'] = [
        'uamqp',
        'aziotsharedutil',
        'AdvAPI32',
        'Crypt32',
        'ncrypt',
        'Secur32',
        'schannel',
        'RpcRT4',
        'WSock32',
        'WS2_32']
elif is_mac:
    kwargs['extra_compile_args'] = ['-g', '-O0', "-std=gnu99", "-fPIC"]
    kwargs['libraries'] = ['uamqp', 'aziotsharedutil']
    if use_openssl and not supress_link_flags:
        kwargs['libraries'].extend(['ssl', 'crypto'])
    elif not use_openssl:
        kwargs['extra_link_args'] = [
            '-framework', 'CoreFoundation',
            '-framework', 'CFNetwork',
            '-framework', 'Security']
else:
    kwargs['extra_compile_args'] = ['-g', '-O0', "-std=gnu99", "-fPIC"]
    # SSL before crypto matters: https://bugreports.qt.io/browse/QTBUG-62692
    kwargs['libraries'] = ['uamqp', 'aziotsharedutil', 'ssl', 'crypto']  # 'uuid'


# If the C file doesn't exist, build the "c_uamqp.c" file
# That's not perfect, since we build it on a "--help", but should be if cloned from source only.
c_uamqp_src = "uamqp/c_uamqp.c"
if not os.path.exists(c_uamqp_src):
    c_uamqp_src = create_cython_file()

sources = [
    c_uamqp_src
]

# Configure the extension

extensions = [
    UAMQPExtension("cmake_uamqp"),
    Extension(
        "uamqp.c_uamqp",
        sources=sources,
        include_dirs=include_dirs,
        **kwargs
    )
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
        "Framework :: Pytest",
    ],
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=["tests"]),
    ext_modules = extensions,
    install_requires=[
        "certifi>=2017.4.17",
    ],
    cmdclass={
        'build_ext': build_ext,
    }    
)
