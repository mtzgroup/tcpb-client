#!/usr/bin/env python
# Basic energy calculation
import sys

from qcio import ProgramInput, Structure

from tcpb import TCProtobufClient as TCPBClient

if len(sys.argv) != 3:
    print("Usage: {} host port\n".format(sys.argv[0]))
    exit(1)


structure = Structure(
    symbols=["O", "H", "H"],
    geometry=[[0.0, 0.0, 0.0], [0.0, 1.5, 0.0], [0.0, 0.0, 1.5]],
)
prog_inp = ProgramInput(
    calctype="energy",  # type: ignore
    structure=structure,
    model={"method": "b3lyp", "basis": "6-31g"},  # type: ignore
)

with TCPBClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    prog_output = client.compute(prog_inp)

print(prog_output)
print(prog_output.results.energy)
