#!/usr/bin/env python
# Simple example showing a TDDFT calculation

import sys

from qcelemental.models import AtomicInput, Molecule
from tcpb import TCFrontEndClient as TCPBClient

# Ethene system
atoms = ["C", "C", "H", "H", "H", "H"]
geom = [
    0.35673483,
    -0.05087227,
    -0.47786734,
    1.61445821,
    -0.06684947,
    -0.02916681,
    -0.14997206,
    0.87780529,
    -0.62680155,
    -0.16786485,
    -0.95561368,
    -0.69426370,
    2.15270896,
    0.84221076,
    0.19314809,
    2.16553127,
    -0.97886933,
    0.15232587,
]

if len(sys.argv) != 3:
    print("Usage: {} host port".format(sys.argv[0]))
    exit(1)

molecule = Molecule(symbols=atoms, geometry=geom)
atomic_input = AtomicInput(
    molecule=molecule,
    driver="gradient",
    model={
        "method": "wpbeh",
        "basis": "6-31g",
    },
    keywords={
        "cis": "yes",
        "cistarget": 1,
        "cisnumstates": 3,
        "closed_shell": True,
        "restricted": True,
        "rc_w": 0.2,
        "cis": "yes",
        "cistarget": 1,
        "cisnumstates": 3,
        "cisrelaxdipole": "yes",
    },
    protocols={"wavefunction": "all", "native_files": "all"},
)
with TCPBClient(host=sys.argv[1], port=int(sys.argv[2])) as TC:

    # Gradient calculation
    result = TC.compute(atomic_input)
    print("Grad Results:\n{}".format(result))

    # Coupling calculation
    # nac_options = tddft_options.copy()
    # nac_options["nacstate1"] = 0
    # nac_options["nacstate2"] = 1
    # # Try to seed as much guess as possible
    # # TODO: Update this one CI and Z vectors are passed through properly
    # nac_options["guess"] = "{}/{}".format(grad_results["job_scr_dir"], "c0")

    # nac_results = TC.compute_job_sync("coupling", geom, "angstrom", **nac_options)
    # print("\nNAC Results:\n{}".format(nac_results))
