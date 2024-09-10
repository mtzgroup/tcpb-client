from google.protobuf.internal.containers import RepeatedScalarFieldContainer
from qcio import ProgramInput

from tcpb import TCProtobufClient as TCPBClient

from .answers import cisno_casci
from .conftest import _round

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
]


def test_cisno_casci(settings, ethylene):
    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        # Add in Ethylene atoms
        base_options = {
            "method": "hf",
            "basis": "6-31g**",
        }
        base_options["atoms"] = ethylene.symbols
        options = dict(base_options, **cisno_options)
        results = TC.compute_job_sync(
            "energy", ethylene.geometry.flatten(), "bohr", **options
        )

    for field in fields_to_check:
        assert _round(results[field]) == _round(cisno_casci.correct_answer[field])


def test_cisno_casci_atomic_input(settings, ethylene, job_output):
    # Construct ProgramInput
    prog_inp = ProgramInput(
        structure=ethylene,
        calctype="energy",
        model={
            "method": "hf",
            "basis": "6-31g**",
        },
        keywords=cisno_options,
    )

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        # Add in Ethylene atoms
        results = TC.compute(prog_inp)

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
