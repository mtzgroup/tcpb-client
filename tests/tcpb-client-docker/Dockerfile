# To build and upload this:
# docker build .
# docker tag [CONTAINER HASH] sseritan/tcpb-client-docker:latest
# docker push sseritan/tcpb-client-docker

FROM alpine:3.10

MAINTAINER Stefan Seritan <sseritan@stanford.edu>

ENV PACKAGES="\
  bash \
  build-base \
  bzip2-dev \
  ca-certificates \
  curl \
  gcc \
  git \
  libffi-dev \
  linux-headers \
  make \
  musl \
  openssl-dev \
  readline-dev \
  sqlite-dev \
  vim \
  zlib-dev"

RUN apk update && apk add $PACKAGES

# Pull newer protobuf than available for Alpine APK
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.3.0/protobuf-cpp-3.3.0.tar.gz 
RUN tar xf protobuf-cpp-3.3.0.tar.gz -C /tmp
WORKDIR /tmp/protobuf-3.3.0
RUN ./configure && make && make install
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Pyenv for multiple python runtimes
WORKDIR /home/
RUN git clone https://github.com/pyenv/pyenv.git /home/.pyenv
ENV PYENV_ROOT /home/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python
RUN pyenv install 3.7.4
RUN pyenv install 3.6.9
RUN pyenv install 3.5.7
RUN pyenv install 2.7.16
RUN pyenv global 3.7.4
RUN pyenv rehash

# Preinstall pip packages to cut down on pipeline time
RUN pip install google protobuf numpy tox tox-pyenv

ENTRYPOINT ["/bin/bash"]
