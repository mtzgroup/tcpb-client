#!/usr/bin/env python
# Basic energy calculation
import sys

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
    driver="energy",
    keywords={"restricted": False},
    # TCFrontEndClient can collect stdout
    # TCFrontEnd can also collect native_files produced by TeraCHem from the computation
    protocols={"wavefunction": "all", "stdout": True, "native_files": "all"},
    # TCFrontEndClient will delete scratch unless scratch_messy: True
    extras={settings.tcfe_keywords: {"scratch_messy": False}},
)

with TCFrontEndClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    result = client.compute(atomic_input)

# NOTE: Addition of stdout field possible with TCFrontendClient
print(result.stdout)
print(result)
print(result.return_result)
print(result.extras["job_extras"])
# native_files will contain orb1a/b files in binary form
print(result.native_files.keys())
