from pathlib import Path
from typing import List

import numpy as np
import qcelemental as qcel
from qcelemental.models import AtomicInput, Molecule
from qcelemental.models.results import AtomicResult

from tcpb.tcpb import TCProtobufClient
from tcpb import terachem_server_pb2 as pb
from tcpb.utils import (
    atomic_input_to_job_input,
    job_output_to_atomic_result,
    mol_to_molecule,
)

from .conftest import _round


def test_atomic_input_to_job_input_cisco_casci_similarity(ethylene):
    """
    Test that the new atomic_input_to_job_input function produces the same protobuf
    messages that Stefan's old method created
    """
    # Dicts of options used according to Stefan's old methodology
    old_methodoloy_options = {
        "method": "hf",
        "basis": "6-31g**",
        "atoms": ethylene["atoms"],
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

    # Construct Geometry in bohr
    geom_angstrom = qcel.Datum("geometry", "angstrom", np.array(ethylene["geometry"]))
    geom_bohr = _round(geom_angstrom.to_units("bohr"))

    # Construct Molecule object
    m_ethylene = Molecule.from_data(
        {
            "symbols": ethylene["atoms"],
            "geometry": geom_bohr,
            "molecular_multiplicity": keywords["spinmult"],
            "molecular_charge": keywords["charge"],
        }
    )

    # Construct AtomicInput
    atomic_input = AtomicInput(
        molecule=m_ethylene,
        driver="energy",
        model={"method": "hf", "basis": "6-31g**"},
        keywords=keywords,
    )

    # Create protobof JobInput using Stefan's old approach
    client = TCProtobufClient("host", 11111)
    stefan_style = client._create_job_input_msg(
        "energy", geom_bohr, "bohr", **{**old_methodoloy_options, **keywords}
    )
    # Create protobuf JobInput using AtomicInput object
    job_input = atomic_input_to_job_input(atomic_input)
    assert job_input == stefan_style


def test_job_output_to_atomic_result(atomic_input, job_output):
    atomic_result = job_output_to_atomic_result(
        atomic_input=atomic_input, job_output=job_output
    )
    assert isinstance(atomic_result, AtomicResult)

    # Check that all types in extras are regular python types (no longer protobuf types)
    for key, value in atomic_result.extras["qcvars"].items():
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


def test_mol_to_molecule_bohr():
    with open(Path(__file__).parent / "test_data" / "water_bohr.pb", "rb") as f:
        mol = pb.Mol()
        mol.ParseFromString(f.read())
    molecule = mol_to_molecule(mol)

    assert [s for s in molecule.symbols] == [a for a in mol.atoms]
    assert list(molecule.geometry.flatten()) == [coord for coord in mol.xyz]
    assert molecule.molecular_multiplicity == mol.multiplicity


def test_mol_to_molecule_angstrom():
    with open(Path(__file__).parent / "test_data" / "water_angstrom.pb", "rb") as f:
        mol = pb.Mol()
        mol.ParseFromString(f.read())
    molecule = mol_to_molecule(mol)

    geom_angstrom = qcel.Datum("geometry", "angstrom", np.array(mol.xyz))
    geom_bohr = geom_angstrom.to_units("bohr")

    assert [s for s in molecule.symbols] == [a for a in mol.atoms]
    assert _round(list(molecule.geometry.flatten())) == _round(
        [coord for coord in geom_bohr]
    )
    assert molecule.molecular_multiplicity == mol.multiplicity