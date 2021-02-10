import numpy as np
import qcelemental as qcel
from qcelemental.models import AtomicInput, Molecule

from tcpb import TCProtobufClient as TCPBClient

from .answers import cisno_casci
from .conftest import _round

base_options = {
    "method": "hf",
    "basis": "6-31g**",
}

cisno_options = {
    # Base options
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

fields_to_check = [
    "charges",
    "dipole_moment",
    "dipole_vector",
    "energy",
    "orb_energies",
    "orb_occupations",
    "cas_transition_dipole",
    "bond_order",
]


def test_cisno_casci(settings, ethylene):

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        # Add in Ethylene atoms
        base_options["atoms"] = ethylene["atoms"]
        options = dict(base_options, **cisno_options)
        results = TC.compute_job_sync(
            "energy", ethylene["geometry"], "angstrom", **options
        )

        for field in fields_to_check:
            assert _round(results[field]) == _round(cisno_casci.correct_answer[field])


def test_cisno_casci_atomic_input(settings, ethylene):
    # Construct Geometry in bohr
    geom_angstrom = qcel.Datum("geometry", "angstrom", np.array(ethylene["geometry"]))
    geom_bohr = geom_angstrom.to_units("bohr")

    # Construct Molecule object
    m_ethylene = Molecule.from_data(
        {
            "symbols": ethylene["atoms"],
            "geometry": geom_bohr,
            "molecular_multiplicity": cisno_options["spinmult"],
            "molecular_charge": cisno_options["charge"],
        }
    )

    # Construct AtomicInput
    atomic_input = AtomicInput(
        molecule=m_ethylene,
        driver="energy",
        model=base_options,
        keywords=cisno_options,
    )

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        # Add in Ethylene atoms
        results = TC.compute(atomic_input)

    for field in fields_to_check:
        assert _round(results[field]) == _round(cisno_casci.correct_answer[field])
