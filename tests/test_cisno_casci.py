import numpy as np
import qcelemental as qcel
from google.protobuf.internal.containers import RepeatedScalarFieldContainer
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


def test_cisno_casci_atomic_input(settings, ethylene, job_output):
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

    # compare only relevant attributes (computed values)
    attrs_to_compare = []
    for attr in dir(results):
        if (
            not (
                attr.startswith("__")
                or attr.startswith("_")
                or callable(attr)
                or attr[0].isupper()
            )
            and attr in fields_to_check
        ):
            attrs_to_compare.append(attr)

    for attr in attrs_to_compare:
        if isinstance(getattr(results, attr), RepeatedScalarFieldContainer):
            assert _round([a for a in getattr(results, attr)]) == _round(
                [a for a in getattr(job_output, attr)]
            )
        else:
            assert getattr(results, attr) == getattr(job_output, attr)
