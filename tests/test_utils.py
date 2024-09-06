from pathlib import Path

import numpy as np
from qcio import ProgramInput, ProgramOutput, constants

from tcpb import terachem_server_pb2 as pb
from tcpb.clients import TCFrontEndClient, TCProtobufClient
from tcpb.utils import (
    mol_to_structure,
    prog_inp_to_job_inp,
)

from .conftest import _round


def test_prog_input_to_job_input_cisco_casci_similarity(ethylene):
    """
    Test that the new prog_input_to_job_input function produces the same protobuf
    messages that Stefan's old method created
    """
    # Dicts of options used according to Stefan's old methodology
    old_methodology_options = {
        "method": "hf",
        "basis": "6-31g**",
        "atoms": ethylene.symbols,
    }
    keywords = {
        # base options
        "charge": 0,
        "spinmult": 1,
        "closed_shell": True,
        "restricted": True,
        "precision": "double",
        "convthre": 1e-8,
        "threall": 1e-20,
        # cisno options
        "cisno": "yes",
        "cisnostates": 2,
        "cisnumstates": 2,
        "closed": 7,
        "active": 2,
        "cassinglets": 2,
        "dcimaxiter": 100,
    }

    # Construct ProgramInput
    prog_input = ProgramInput(
        structure=ethylene,
        calctype="energy",
        model={"method": "hf", "basis": "6-31g**"},
        keywords=keywords,
    )

    # Create protobof JobInput using Stefan's old approach
    client = TCProtobufClient("host", 11111)
    stefan_style = client._create_job_input_msg(
        "energy",
        ethylene.geometry.flatten(),
        "bohr",
        **{**old_methodology_options, **keywords},
    )
    # Create protobuf JobInput using ProgramInput object
    job_input = prog_inp_to_job_inp(prog_input)
    assert job_input == stefan_style


def test_job_output_to_prog_output(prog_input, job_output):
    client = TCProtobufClient()
    prog_output = client.job_output_to_atomic_result(
        inp_data=prog_input, job_output=job_output
    )
    assert isinstance(prog_output, ProgramOutput)

    # Check that all types in extras are regular python types (no longer protobuf types)
    for key, value in prog_output.extras.items():
        assert isinstance(key, str)
        assert (
            isinstance(
                value,
                (
                    list,
                    float,
                    int,
                    str,
                    bool,
                ),
            )
            or value is None
        )


def test_job_output_to_prog_output_correctly_sets_provenance(prog_input, job_output):
    pb_client = TCProtobufClient()
    prog_output = pb_client.job_output_to_atomic_result(
        inp_data=prog_input, job_output=job_output
    )
    assert isinstance(prog_output, ProgramOutput)
    assert prog_output.provenance.program == pb_client.program

    fe_client = TCFrontEndClient()
    prog_output = fe_client.job_output_to_atomic_result(
        inp_data=prog_input, job_output=job_output
    )
    assert isinstance(prog_output, ProgramOutput)
    assert prog_output.provenance.program == fe_client.program


def test_mol_to_struct_bohr():
    with open(Path(__file__).parent / "test_data" / "water_bohr.pb", "rb") as f:
        mol = pb.Mol()
        mol.ParseFromString(f.read())
    struct = mol_to_structure(mol)

    assert [s for s in struct.symbols] == [a for a in mol.atoms]
    assert list(struct.geometry.flatten()) == [coord for coord in mol.xyz]
    assert struct.multiplicity == mol.multiplicity


def test_mol_to_struct_angstrom():
    with open(Path(__file__).parent / "test_data" / "water_angstrom.pb", "rb") as f:
        mol = pb.Mol()
        mol.ParseFromString(f.read())
    struct = mol_to_structure(mol)

    assert [s for s in struct.symbols] == [a for a in mol.atoms]
    assert _round(list(struct.geometry.flatten())) == _round(
        [coord for coord in np.array(mol.xyz) * constants.ANGSTROM_TO_BOHR]
    )
    assert struct.multiplicity == mol.multiplicity
