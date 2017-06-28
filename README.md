# TeraChem Protocol Buffer (TCPB) Python Client #

A Python client for communicating directly with a TeraChem Protocol Buffer (TCPB) server.

## Installation ##
Download the repo and install the TCPB Python client into a local Conda environment:

1. `git clone git@bitbucket.org:mtzcloud/tcpb-client.git`
2. `cd tcpb-client`
3. `source activate <target environment>`
4. `python setup.py install`

## Example Client ##
Assuming there is a TCPB server running on port 54321 on localhost (see TCPB Server section below),
you can run the example Python script with `python tcpb-example.py`.


## Contents ##
* `tcpb.py`: Contains TCProtobufClient class, wrapping the generated Protocol Buffer code
into a more user-friendly client

* `protobuf/`: Contains the definition of the Protocol Buffer (terachem_server.proto) and the generated
Protocol Buffer code (terachem_server_pb2.py)
 * Compile terachem_server.proto into the generated code with: `protoc terachem_server.proto --python_out=.`

## TCPB Server ##
TCPB servers are run using the --server/-s flag (and often using the --gpus/-g flag).
For example, `terachem -s 54321 -g 01` starts a TCPB server listening on port 54321
with 2 GPUs (numbered 0 and 1 as per `nvidia-smi`)
