# TeraChem Protocol Buffer (TCPB) Python Client #

A Python client for communicating directly with a TeraChem Protocol Buffer (TCPB) server.

## Getting Started ##

## Example Client ##

## Contents ##
* `tcpb.py`:

* `protobuf/`:

## TCPB Server ##
TCPB servers are run using the --server/-s flag (and often using the --gpus/-g flag).
For example,

'''
terachem -s 54321 -g 01
'''

starts a TCPB server listening on port 54321 and 2 GPUs (numbered 0 and 1 as per `nvidia-smi`)
