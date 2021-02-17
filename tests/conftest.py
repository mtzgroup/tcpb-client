from typing import Collection, Union
from pathlib import Path

import pytest
from qcelemental.models import Molecule, AtomicInput
from qcelemental.models.common_models import Model

from tcpb import terachem_server_pb2 as pb


@pytest.fixture
def settings():
    yield {"tcpb_host": "localhost", "tcpb_port": 11111, "round_decimals": 6}


@pytest.fixture
def ethylene():
    # NOTE: Geometry in angstroms
    yield {
        "atoms": ["C", "C", "H", "H", "H", "H"],
        "geometry": [
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
        ],
    }


@pytest.fixture(scope="function")
def water():
    return Molecule.from_data(
        """
        -1 2
        O 0 0 0
        H 0 0 1
        H 0 1 0
        """
    )


@pytest.fixture(scope="function")
def atomic_input(water):
    model = Model(method="B3LYP", basis="6-31g")
    return AtomicInput(molecule=water, model=model, driver="energy")


@pytest.fixture
def job_output():
    """Return job_output protobuf message"""
    job_output_correct_answer = pb.JobOutput()
    with open(
        Path(__file__).parent / "answers" / "cisno_casci_result.pbmsg", "rb"
    ) as f:
        job_output_correct_answer.ParseFromString(f.read())
    return job_output_correct_answer


def _round(value: Union[Collection[float], float], places: int = 6):
    """Round a value or Collection of values to a set precision"""
    if isinstance(value, (float, int)):
        return round(value, places)
    elif isinstance(value, Collection):
        return [_round(v, places) for v in value]
    else:
        raise ValueError(f"Cannot round value of type {type(value)}")
