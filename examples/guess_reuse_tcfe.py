#!/usr/bin/env python
# Basic energy calculation
import sys

from qcio import CalcType, ProgramInput, Structure

from tcpb import TCFrontEndClient

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} host port")
    exit(1)


struct = Structure(
    symbols=["O", "H", "H"], geometry=[0.0, 0.0, 0.0, 0.0, 1.5, 0.0, 0.0, 0.0, 1.5]
)
prog_inp = ProgramInput(
    calctype=CalcType.energy,
    structure=struct,
    model={"method": "b3lyp", "basis": "6-31g"},  # type: ignore
    # Density matrix purification appears buggy and messes with initial guess
    keywords={"purify": "no"},
)

with TCFrontEndClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    prog_output = client.compute(prog_inp, collect_files=True)

prog_inp_2 = prog_inp.model_dump()
prog_inp_2["files"]["c0"] = prog_output.results.files["scr/c0"]

with TCFrontEndClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    prog_output_2 = client.compute(ProgramInput(**prog_inp_2))

print(prog_output.stdout)
print(prog_output_2.stdout)
