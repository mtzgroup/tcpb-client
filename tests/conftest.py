from typing import Collection, Union

import pytest


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


def _round(value: Union[Collection[float], float], places: int = 6):
    """Round a value or Collection of values to a set precision"""
    if isinstance(value, (float, int)):
        return round(value, places)
    elif isinstance(value, Collection):
        return [_round(v, places) for v in value]
    else:
        raise ValueError(f"Cannot round value of type {type(value)}")
