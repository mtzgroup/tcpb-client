#!/usr/bin/env python
# Basic energy calculation
import sys

from tcpb import TCProtobufClient as TCPBClient
from qcelemental.models import Molecule, AtomicInput

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
        "method": "pbe0",
        "basis": "6-31g",
    },
    driver="energy",
    keywords={"closed_shell": True, "restricted": True},
)

with TCPBClient(host=sys.argv[1], port=int(sys.argv[2])) as TC:
    result = TC.compute(atomic_input)

print(result)
print(result.return_result)
