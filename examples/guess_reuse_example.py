#!/usr/bin/env python
# Guess reuse example

import os
import sys

from tcpb import TCProtobufClient

# Water system
atoms = ["O", "H", "H"]
geom = [
    0.00000,
    0.00000,
    -0.06852,
    0.00000,
    -0.79069,
    0.54370,
    0.00000,
    0.79069,
    0.54370,
]
# Default geom is bohr, but this in angstrom

if len(sys.argv) != 3:
    print("Usage: {} host port".format(sys.argv[0]))
    exit(1)

with TCProtobufClient(host=sys.argv[1], port=int(sys.argv[2])) as TC:
    tc_opts = {
        "atoms": atoms,
        "charge": 0,
        "spinmult": 1,
        "closed_shell": True,
        "restricted": True,
        "method": "pbe0",
        "basis": "6-31g",
        # necessary to avoid density matrix purification on second calc which will
        # cause second calc to begin at different starting point than where first cals
        # ended
        "purify": "no",
    }

    results = TC.compute_job_sync("gradient", geom, "bohr", **tc_opts)

    # We can pull the orbital path from the previous job to feed in as a guess
    orb_path = os.path.join(results["job_scr_dir"], "c0")
    results = TC.compute_job_sync("gradient", geom, "bohr", guess=orb_path, **tc_opts)

    # Things look slightly different for unrestricted guesses
    tc_opts["closed_shell"] = False
    tc_opts["restricted"] = False
    results = TC.compute_job_sync("gradient", geom, "angstrom", **tc_opts)

    # TeraChem expects "guess <ca0 file> <cb0 file>"
    orb_paths = "{0}/ca0 {0}/cb0".format(results["job_scr_dir"])
    print(orb_paths)
    results = TC.compute_job_sync(
        "gradient", geom, "angstrom", guess=orb_paths, **tc_opts
    )
