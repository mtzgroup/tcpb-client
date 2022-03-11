from pathlib import Path
from typing import Collection, Union

import pytest
from qcelemental.models import (
    AtomicInput,
    AtomicResult,
    AtomicResultProperties,
    Molecule,
)
from qcelemental.models.common_models import Model

from tcpb import terachem_server_pb2 as pb
from tcpb.config import settings as tcpb_settings


@pytest.fixture
def settings():
    yield {"tcpb_host": "localhost", "tcpb_port": 11111, "round_decimals": 6}


@pytest.fixture
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "test_data"


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
    return Molecule(
        symbols=["O", "H", "H"],
        geometry=[0.0, 0.0, 0.0, 0.0, 1.5, 0.0, 0.0, 0.0, 1.5],  # in bohr
    )


@pytest.fixture(scope="function")
def atomic_input(water):
    model = Model(method="B3LYP", basis="6-31g")
    return AtomicInput(molecule=water, model=model, driver="energy")


@pytest.fixture(scope="function")
def atomic_result(atomic_input):
    result = AtomicResult(
        **atomic_input.dict(),
        return_result=123.123,
        success=True,
        properties=AtomicResultProperties(return_energy=123.123),
    )
    result.extras[tcpb_settings.extras_job_kwarg] = {"job_dir": "job_1"}
    return result


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
