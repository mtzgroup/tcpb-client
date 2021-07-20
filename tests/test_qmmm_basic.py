from pathlib import Path

import numpy as np
from tcpb.models import Mol, JobInput, JobOutput

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

    mol_qm_water = Mol(
        atoms = qm_atoms,
        xyz = qm_geom,
        units = "Angstrom",
        charge = 0,
        multiplicity = 1,
        closed = True,
        restricted = True,
    )

    jobinput = JobInput(
        mol = mol_qm_water,
        method_type = "HF",
        run = "gradient",
        basis = "3-21g",
        prmtop_path = str(prmtop_file),
        mm_xyz = mm_geom,
        qm_indices = qm_indices,
    )

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        results = TC.compute_py(jobinput)

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
        assert _round(getattr(results, field), 5) == _round(
            qmmm_basic.correct_answer[field], 5
        )
