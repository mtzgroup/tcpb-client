#!/usr/bin/env python
# Basic energy calculation
import sys

from qcio import ProgramInput, Structure

from tcpb import TCFrontEndClient

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} host port")
    exit(1)


structure = Structure(
    symbols=["O", "H", "H"], geometry=[0.0, 0.0, 0.0, 0.0, 1.5, 0.0, 0.0, 0.0, 1.5]
)
atomic_input = ProgramInput(
    structure=structure,
    model={"method": "b3lyp", "basis": "6-31g"},  # type: ignore
    calctype="energy",  # type: ignore
    keywords={"restricted": False},
)

with TCFrontEndClient(host=sys.argv[1], port=int(sys.argv[2])) as client:
    # Collect stdout and native files
    prog_output = client.compute(atomic_input, collect_stdout=True, collect_files=True)

# NOTE: Addition of stdout field possible with TCFrontendClient
print(prog_output.stdout)
print(prog_output)
print(prog_output.return_result)
# native_files will contain orb1a/b files in binary form
print(prog_output.files.keys())
