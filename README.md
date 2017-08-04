# TeraChem Protocol Buffer (TCPB) Client #

This repository is designed to facilitate the development of C++ and Python clients for communicating with TeraChem.

These clients use C-style sockets for communication, and Protocol Buffers for a clean, well-defined way to serialize TeraChem input & output.

## MPI Engine vs. TCPB vs. PyTC: Why Do We Have So Many Clients for TeraChem?

There are three projects that are being developed in parallel: the MPI SinglePoint engine, these TCPB clients, and the PyTC client, which is part of larger TeraChem-Cloud project.
In the long-term, PyTC is undoubtedly the way to go, hiding all the load balancing, robust data storage solutions, simple parallelization over TeraChem instances,
and easy job submission and retrieval from anywhere, so long as you have an internet connection.

However, it will be a few more months before that system is fully operational.
So in the short-term, TCPB clients are the fastest way to use non-MPI TeraChem server instances.
Currently, TCPB clients and the MPI SinglePoint engine are comparable in functionality, but the current trend is to move away from MPI when we can.

Additionally, some projects are more well suited to interacting tightly with a single server (e.g. interactive MD).
For these projects, the TCPB clients make the most sense.

All three clients will have similar job setup and convenience functions, so if you stay away from calling any protobuf-specific code,
you should be able to swap the clients easily.


For more information, see the [Wiki](https://bitbucket.org/sseritan/tcpb-client/wiki/Home).