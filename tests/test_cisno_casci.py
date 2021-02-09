from tcpb import TCProtobufClient as TCPBClient

from .conftest import _round


def test_cisno_casci(settings, ethylene):
    from .answers import cisno_casci_example

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        base_options = {
            "method": "hf",
            "basis": "6-31g**",
            "atoms": ethylene["atoms"],
            "charge": 0,
            "spinmult": 1,
            "closed_shell": True,
            "restricted": True,
            "precision": "double",
            "convthre": 1e-8,
            "threall": 1e-20,
        }

        cisno_options = {
            "cisno": "yes",
            "cisnostates": 2,
            "cisnumstates": 2,
            "closed": 7,
            "active": 2,
            "cassinglets": 2,
            "dcimaxiter": 100,
        }
        options = dict(base_options, **cisno_options)
        results = TC.compute_job_sync("energy", ethylene["geom"], "angstrom", **options)

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
        for field in fields_to_check:
            assert _round(results[field]) == _round(
                cisno_casci_example.correct_answer[field]
            )
