from pathlib import Path

import numpy as np
import qcelemental as qcel
from qcelemental.models import AtomicInput, Molecule
from google.protobuf.internal.containers import RepeatedScalarFieldContainer

from tcpb import TCProtobufClient as TCPBClient

from .answers import qmmm_basic
from .conftest import _round


def test_qmmm_basic(settings):

    # QM water, geom in angstrom
    qm_atoms = ["O", "H", "H"]
    qm_geom = [
        -0.8680000, 0.0960000, 0.0000000,
        0.0920000, 0.0960000, 0.0000000,
        -1.1890000, 1.0010000, 0.0000000,
    ]
    qm_indices = [0, 1, 2]
    # MM water, geom in angstrom
    mm_geom = [
        2.1560000, 0.0960000, 0.0000000,
        2.8820000, 0.1870000, -0.6220000,
        2.5070000, -0.0330000, 0.8840000,
    ]
    prmtop_file = Path(__file__).parent / "test_data" / "2water.prmtop"

    qm_geom_angstrom = qcel.Datum("geometry", "angstrom", np.array(qm_geom))
    qm_geom_bohr = qm_geom_angstrom.to_units("bohr")
    mm_geom_angstrom = qcel.Datum("geometry", "angstrom", np.array(mm_geom))
    mm_geom_bohr = mm_geom_angstrom.to_units("bohr")

    # Construct Molecule object
    m_qm_water = Molecule.from_data(
        {
            "symbols": qm_atoms,
            "geometry": qm_geom_bohr,
            "molecular_multiplicity": 1,
            "molecular_charge": 0,
        }
    )

    # Construct AtomicInput
    atomic_input = AtomicInput(
        molecule = m_qm_water,
        driver = "gradient",
        model = {
            "method": "hf",
            "basis": "3-21g",
        },
        keywords = {
            "closed_shell": True,
            "restricted": True,
            "prmtop": prmtop_file,
            "mm_geometry": mm_geom_bohr,
            "qm_indices": qm_indices,
        }
    )

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        # Add in Ethylene atoms
        results = TC.compute(atomic_input)
        results = results.extras["qcvars"]

    fields_to_check = [
        "charges",
        "dipole_moment",
        "dipole_vector",
        "energy",
        "gradient",
        "mm_gradient",
        # "orb_energies",
        # "orb_occupations",
        # "bond_order",
    ]

    print(results)

    for field in fields_to_check:
        assert _round(results[field], 5) == _round(
            qmmm_basic.correct_answer[field], 5
        )
