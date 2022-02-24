#!/usr/bin/env python
# Basic energy calculation
import sys

from qcelemental.models import AtomicInput, Molecule

from tcpb import TCProtobufClient as TCPBClient

if len(sys.argv) != 3:
    print("Usage: {} host port".format(sys.argv[0]))
    exit(1)


# Water system
atoms = ["O", "H", "H"]
geom = [0.0, 0.0, 0.0, 0.0, 1.5, 0.0, 0.0, 0.0, 1.5]  # in bohr

molecule = Molecule(symbols=atoms, geometry=geom)
atomic_input = AtomicInput(
    molecule=molecule,
    model={
        "method": "b3lyp",
        "basis": "6-31g",
    },
    driver="energy",
    protocols={"wavefunction": "all"},
)

with TCPBClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    result = client.compute(atomic_input)

print(result)
print(result.return_result)
