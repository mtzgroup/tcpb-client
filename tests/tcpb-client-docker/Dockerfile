# To build and upload this:
# docker build .
# docker tag [CONTAINER HASH] sseritan/tcpb-client-docker:latest
# docker push sseritan/tcpb-client-docker

FROM python:3.7

MAINTAINER Stefan Seritan <sseritan@stanford.edu>

# Pull newer protobuf than available for Alpine APK
RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.3.0/protobuf-cpp-3.3.0.tar.gz 
RUN tar xf protobuf-cpp-3.3.0.tar.gz -C /tmp
WORKDIR /tmp/protobuf-3.3.0
RUN ./configure && make && make install
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH


# Preinstall pip packages to cut down on pipeline time
WORKDIR /
RUN pip install google protobuf numpy tox

ENTRYPOINT ["/bin/bash"]
