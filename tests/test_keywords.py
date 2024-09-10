import time

import numpy as np
import pytest

from tcpb import TCProtobufClient as TCPBClient


@pytest.mark.skip(
    reason="You can see in the tc.in/out files the convergence is set correctly. Yes a"
    "looser convergence doesn't always produce a shorter computation time."
)
def test_convthre(settings, prog_input):
    prog_input.keywords["convthre"] = 3.0e-5
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as client:
        start = time.time()
        client.compute(prog_input)
        tight_thresh = time.time() - start

    prog_input.keywords["convthre"] = 3.0e-1
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as client:
        start = time.time()
        client.compute(prog_input)
        looser_thresh = time.time() - start

    assert tight_thresh > looser_thresh


def test_wavefunction(settings, prog_input):
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as TC:
        prog_output = TC.compute(prog_input)

    # Restricted
    assert prog_output.results.wavefunction is not None
    assert isinstance(prog_output.results.wavefunction.scf_eigenvalues_a, np.ndarray)
    assert isinstance(prog_output.results.wavefunction.scf_occupations_a, np.ndarray)
    np.testing.assert_equal(prog_output.results.wavefunction.scf_eigenvalues_b, np.array([]))
    np.testing.assert_equal(prog_output.results.wavefunction.scf_occupations_b, np.array([]))

    prog_input.keywords["restricted"] = False
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as TC:
        prog_output = TC.compute(prog_input)

    # B occupations since restricted=False
    assert prog_output.results.wavefunction is not None
    assert isinstance(prog_output.results.wavefunction.scf_eigenvalues_a, np.ndarray)
    assert isinstance(prog_output.results.wavefunction.scf_occupations_a, np.ndarray)
    assert isinstance(prog_output.results.wavefunction.scf_eigenvalues_b, np.ndarray)
    assert isinstance(prog_output.results.wavefunction.scf_occupations_b, np.ndarray)
