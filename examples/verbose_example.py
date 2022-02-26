#!/usr/bin/env python
# Basic TCProtobufClient usage
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

# Set up client for h2o job
TC = TCProtobufClient(host=sys.argv[1], port=int(sys.argv[2]))

tc_opts = {
    "atoms": atoms,
    "charge": 0,
    "spinmult": 1,
    "closed_shell": True,
    "restricted": True,
    "method": "pbe0",
    "basis": "6-31g",
}

TC.connect()

# Check if the server is available
avail = TC.is_available()
print("TCPB Server available: {}".format(avail))

# Energy calculation
# energy = TC.compute_energy(geom, "angstrom", **tc_opts)  # Default is BOHR
# print("H2O Energy: {}".format(energy))

# Gradient calculation
# energy, gradient = TC.compute_gradient(geom, "angstrom", **tc_opts)
result = TC.compute_job_sync("gradient", geom, "angstrom", **tc_opts)
print(result)
print("H2O Gradient:\n{}".format(result["gradient"]))

# # Forces calculation (just like gradient call with -1*gradient)
# energy, forces = TC.compute_forces(geom, "angstrom", **tc_opts)
# print("H2O Forces:\n{}".format(forces))

# # General calculation
# results = TC.compute_job_sync("gradient", geom, "angstrom", **tc_opts)
# print("H2O Results:\n{}".format(results))

# # Can get information from last calculation
# print("Last H2O Energy: {}".format(TC.prev_results["energy"]))

TC.disconnect()
