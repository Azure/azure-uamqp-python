# internal users should provide MCR registry to build via 'docker build . --build-arg REGISTRY="mcr.microsoft.com/mirror/docker/library/"'
# public OSS users should simply leave this argument blank or ignore its presence entirely
ARG REGISTRY="mcr.microsoft.com/mirror/docker/library/"
FROM ${REGISTRY}ubuntu:18.04

# To test a script:
# docker run --rm -it -v %cd%:/data local/valgrind
# python3.6 -m pip install -e .
# valgrind --tool=memcheck --suppressions=valgrind-python.supp --leak-check=full python3.6 ./test_script.py &> valgrind_log.txt

# Install Python 3.6
RUN apt-get update
RUN apt-get install -y software-properties-common vim
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv libc6-dbg curl
RUN apt-get install -y libssl-dev uuid-dev cmake libcurl4-openssl-dev pkg-config

# update pip
RUN python3.6 -m pip install pip --upgrade
RUN python3.6 -m pip install wheel cython


# Install Valgrind
RUN cd /tmp && \
    curl -O ftp://sourceware.org/pub/valgrind/valgrind-3.13.0.tar.bz2 && \
    tar xvf valgrind-3.13.0.tar.bz2 && \
    cd valgrind-3.13.0 && \
    ./configure && \
    make && \
    make install

ENV PYTHONMALLOC=malloc
ENTRYPOINT [ "/bin/bash" ]