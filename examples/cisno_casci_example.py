#!/usr/bin/env python
# Simple example showing a CISNO-CASCI calculation

import sys

from tcpb import TCProtobufClient as TCPBClient

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

with TCPBClient(host=sys.argv[1], port=int(sys.argv[2])) as TC:
    base_options = {
        "method": "hf",
        "basis": "6-31g**",
        "atoms": atoms,
        "charge": 0,
        "spinmult": 1,
        "closed_shell": True,
        "restricted": True,
        "precision": "double",
        "convthre": 1e-8,
        "threall": 1e-20,
    }

    cisno_options = {
        "cisno": "yes",
        "cisnostates": 2,
        "cisnumstates": 2,
        "closed": 7,
        "active": 2,
        "cassinglets": 2,
        "dcimaxiter": 100,
    }
    options = dict(base_options, **cisno_options)
    results = TC.compute_job_sync("energy", geom, "angstrom", **options)
    print(results)
