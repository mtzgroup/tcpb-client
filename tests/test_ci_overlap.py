import os

import numpy as np
import qcelemental as qcel
from qcelemental.models import AtomicInput, Molecule
from google.protobuf.internal.containers import RepeatedScalarFieldContainer

from tcpb import TCProtobufClient as TCPBClient

from .answers import ci_overlap
from .conftest import _round

# Ethylene system
atoms = ["C", "C", "H", "H", "H", "H"]
geom = [
    0.35673483,
    -0.05087227,
    -0.47786734,
    1.61445821,
    -0.06684947,
    -0.02916681,
    -0.14997206,
    0.87780529,
    -0.62680155,
    -0.16786485,
    -0.95561368,
    -0.69426370,
    2.15270896,
    0.84221076,
    0.19314809,
    2.16553127,
    -0.97886933,
    0.15232587,
]
geom2 = [
    0.35673483,
    -0.05087227,
    -0.47786734,
    1.61445821,
    -0.06684947,
    -0.02916681,
    -0.14997206,
    0.87780529,
    -0.62680155,
    -0.16786485,
    -0.95561368,
    -0.69426370,
    2.15270896,
    0.84221076,
    0.19314809,
    2.16553127,
    -0.97886933,
    0.15232587,
]

essential_options = {
    "method": "hf",
    "basis": "6-31g**",
}

base_options = {
    "charge": 0,
    "spinmult": 1,
    "closed_shell": True,
    "restricted": True,
    "precision": "double",
    "threall": 1.0e-20,
    "casci": "yes",
    "closed": 5,
    "active": 6,
    "cassinglets": 10,
}

casci_options = {"directci": "yes", "caswritevecs": "yes"}

fields_to_check = [
    "charges",
    "spins",
    "dipole_moment",
    "dipole_vector",
    "orb_energies",
    "orb_occupations",
    "ci_overlap",
    "bond_order",
]

# TODO: This test sometimes causes "Bus error (core dumped)" for terachem server
def test_ci_overlap(settings):

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:

        # First run CASCI to get some test CI vectors
        base_options["atoms"] = atoms
        options = dict(essential_options, **base_options, **casci_options)
        results = TC.compute_job_sync("energy", geom, "angstrom", **options)

        # Run ci_vec_overlap job based on last job
        overlap_options = {
            "geom2": geom2,
            "cvec1file": os.path.join(results["job_scr_dir"], "CIvecs.Singlet.dat"),
            "cvec2file": os.path.join(results["job_scr_dir"], "CIvecs.Singlet.dat"),
            "orb1afile": os.path.join(results["job_scr_dir"], "c0"),
            "orb2afile": os.path.join(results["job_scr_dir"], "c0"),
        }
        options = dict(essential_options, **base_options, **overlap_options)
        results = TC.compute_job_sync("ci_vec_overlap", geom, "angstrom", **options)

        for field in fields_to_check:
            assert _round(results[field]) == _round(ci_overlap.correct_answer[field])


# def test_ci_overlap_atomic_input(settings):
#     # Construct Geometry in bohr
#     geom_angstrom = qcel.Datum("geometry", "angstrom", np.array(geom))
#     geom_bohr = geom_angstrom.to_units("bohr")
#     geom2_angstrom = qcel.Datum("geometry", "angstrom", np.array(geom2))
#     geom2_bohr = geom2_angstrom.to_units("bohr")

#     # Construct Molecule object
#     m_ethylene = Molecule.from_data(
#         {
#             "symbols": atoms,
#             "geometry": geom_bohr,
#             "molecular_multiplicity": base_options["spinmult"],
#             "molecular_charge": base_options["charge"],
#         }
#     )

#     # Construct AtomicInput
#     atomic_input = AtomicInput(
#         molecule = m_ethylene,
#         driver = "energy",
#         model = essential_options,
#         keywords = dict(base_options, **casci_options),
#     )

#     with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
#         # Add in Ethylene atoms
#         results = TC.compute(atomic_input)

#     job_scr_dir = results.extras["qcvars"]["job_scr_dir"]
#     # Run ci_vec_overlap job based on last job
#     overlap_options = {
#         "geom2": geom2_bohr,
#         "cvec1file": os.path.join(job_scr_dir, "CIvecs.Singlet.dat"),
#         "cvec2file": os.path.join(job_scr_dir, "CIvecs.Singlet.dat"),
#         "orb1afile": os.path.join(job_scr_dir, "c0"),
#         "orb2afile": os.path.join(job_scr_dir, "c0"),
#     }

#     # Construct new AtomicInput
#     atomic_input = AtomicInput(
#         molecule = m_ethylene,
#         driver = "ci_vec_overlap", # TODO: This driver option is not working
#         model = essential_options,
#         keywords = dict(base_options, **overlap_options),
#     )
    
#     with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
#         # Add in Ethylene atoms
#         results = TC.compute(atomic_input)

#     for attr in fields_to_check:
#         if isinstance(getattr(results, attr), RepeatedScalarFieldContainer):
#             assert _round([a for a in getattr(results, attr)]) == _round(
#                 [a for a in getattr(job_output, attr)]
#             )
#         else:
#             assert getattr(results, attr) == getattr(job_output, attr)
