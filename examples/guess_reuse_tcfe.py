#!/usr/bin/env python
# Basic energy calculation
import sys
from pprint import pprint

from qcelemental.models import AtomicInput, Molecule

from tcpb import TCFrontEndClient
from tcpb.config import settings

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} host port")
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
    # Density matrix purification appears buggy and messes with initial guess
    keywords={"purify": "no"},
    driver="energy",
    protocols={"wavefunction": "all", "stdout": True, "native_files": "all"},
)

with TCFrontEndClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    result = client.compute(atomic_input)

atomic_input_2 = atomic_input.dict()
atomic_input_2["extras"] = {settings.tcfe_keywords: {}}
atomic_input_2["extras"][settings.tcfe_keywords]["c0"] = result.native_files["c0"]
atomic_input_2["extras"][settings.tcfe_keywords]["uploads_messy"] = False

with TCFrontEndClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    result2 = client.compute(AtomicInput(**atomic_input_2))

print(result)
print(result.return_result)

pprint(result.stdout)
pprint(result2.stdout)
