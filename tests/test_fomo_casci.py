import pytest

from tcpb import TCProtobufClient as TCPBClient

from .answers import fomo_casci
from .conftest import _round


@pytest.mark.skip(
    "Fails for reasons internal to TeraChem. It appears this method causes TeraChem (or the PBS?) to return"
    "vastly different results than previously. See https://github.com/mtzgroup/terachem/issues/139"
)
def test_fomo_casci(settings, ethylene):

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        options = {
            "method": "hf",
            "basis": "6-31g**",
            "atoms": ethylene["atoms"],
            "charge": 0,
            "spinmult": 1,
            "closed_shell": True,
            "restricted": True,
            "precision": "double",
            "threall": 1e-20,
            "casci": "yes",
            "fon": "yes",
            "closed": 7,
            "active": 2,
            "cassinglets": 2,
            "nacstate1": 0,
            "nacstate2": 1,
        }

        # NACME calculation
        results = TC.compute_job_sync(
            "coupling", ethylene["geometry"], "angstrom", **options
        )

        fields_to_check = [
            "charges",
            "dipole_moment",
            "dipole_vector",
            "energy",
            "orb_energies",
            "orb_occupations",
            "nacme",
            "cas_transition_dipole",
            "cas_energy_labels",
            "bond_order",
        ]

        for field in fields_to_check:
            assert _round(results[field], 4) == _round(
                fomo_casci.correct_answer[field], 4
            )
        print(results)
