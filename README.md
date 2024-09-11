# Python TeraChem Protocol Buffer (TCPB) Client

[![image](https://img.shields.io/pypi/v/tcpb.svg)](https://pypi.python.org/pypi/tcpb)
[![image](https://img.shields.io/pypi/l/tcpb.svg)](https://pypi.python.org/pypi/tcpb)
[![image](https://img.shields.io/pypi/pyversions/tcpb.svg)](https://pypi.python.org/pypi/tcpb)
[![Actions status](https://github.com/mtzgroup/tcpb-client/workflows/Basic%20Code%20Quality/badge.svg)](https://github.com/mtzgroup/tcpb-client/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

See the [documentation](https://mtzgroup.github.io/tcpb-client/)

Python client to communicate with TeraChem running in server mode.

Client uses C-style sockets for communication and Protocol Buffers for data serialization.

## Requirements

- Python 3.9+

## Installation

```sh
pip install tcpb
```

## Notes

The original, Python 2.7 compatible `tcpb` client built by Stefan Seritan was released as version `0.6.0`. If you depend upon this original release it can be installed by pegging to its version:

```sh
pip install tcpb==0.6.0
```

All future releases will support Python 3+ and MolSSI's QCSchema for data input/output.
