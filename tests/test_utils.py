import numpy as np
import qcelemental as qcel
from qcelemental.models import AtomicInput, Molecule

from tcpb.tcpb import TCProtobufClient
from tcpb.utils import atomic_input_to_job_input

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
