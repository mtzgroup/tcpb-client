# TeraChem Protocol Buffer (TCPB) Client #

C++ and Python clients for communicating directly with a TeraChem Protocol Buffer (TCPB) server.


## Contents ##
* `cpp/`: `tcpb.cpp` contains the C++ TCProtobufClient class, wrapping the generated
Protocol Buffer code (`terachem_server.pb.cc/.h`)

* `proto/`: Contains the .proto file that defines the TeraChem Protocol Buffer.
Compile with `protoc terachem_server.proto --python_out=../python/tcpb/ --cpp_out=../cpp/`

* `python/`: `tcpb.py` contains the TCProtobufClient class, wrapping the generated
Protocol Buffer code (`terachem_server_pb2.py`)

## TCPB Server ##
TCPB servers are run using the --server/-s flag and the --gpus/-g flag.
For example, `terachem -s 54321 -g 01` starts a TCPB server listening on port 54321
with GPUs 0 and 1 (numbered as per `nvidia-smi`)

## Python ##

### Installation ###
Download the repo and install the TCPB Python client into a local Conda environment:

1. `git clone git@bitbucket.org:mtzcloud/tcpb-client.git`
2. `cd tcpb-client/python/`
3. `source activate <target environment>` (use `conda create --name <target environment> pip`
to create a new environment with `python` and `pip` if you don't already have one)
4. `python setup.py install`

You should now be able to run `python -c "import tcpb"` with no errors.

### Example Client ###
Assuming there is a TCPB server running on port 54321 on localhost (see TCPB Server section above),
you can run the example Python script with `python tcpb-example.py`.
