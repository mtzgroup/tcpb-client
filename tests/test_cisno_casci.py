# Simple example showing a CISNO-CASCI calculation
import sys
from tcpb import TCProtobufClient as TCPBClient

# Ethene system

import pytest

@pytest.mark.skip
def test_cisno_casci(settings, ethylene):

    with TCPBClient(host=settings["tcpb_host"], port=settings["tcpb_port"]) as TC:
        base_options = {
            "method": "hf",
            "basis": "6-31g**",
            "atoms": ethylene['atoms'],
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
        print(results)