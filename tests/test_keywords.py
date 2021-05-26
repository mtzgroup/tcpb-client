import time

from numpy import ndarray
from qcelemental.models import AtomicInput

from tcpb import TCProtobufClient as TCPBClient


def test_molden_file_creation(settings, atomic_input, test_data_dir):
    # Add molden keywords
    atomic_input.keywords.update({"mo_output": True, "molden": True})
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as TC:
        result = TC.compute(atomic_input)

    with open(test_data_dir / "water.molden") as f:
        correct_molden = f.read()

    assert result.extras["molden"] == correct_molden


def test_convthre(settings, atomic_input):
    atomic_input.keywords["convthre"] = 3.0e-5
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as TC:
        start = time.time()
        TC.compute(atomic_input)
        tight_thresh = time.time() - start

    atomic_input.keywords["convthre"] = 3.0e-2
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as TC:
        start = time.time()
        TC.compute(atomic_input)
        looser_thresh = time.time() - start

    assert tight_thresh > looser_thresh


def test_wavefunction(settings, atomic_input):
    atomic_input_dict = atomic_input.dict()
    atomic_input_dict.pop("protocols", None)
    with_wf = AtomicInput(**atomic_input_dict, protocols={"wavefunction": "all"})
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as TC:
        result = TC.compute(with_wf)

    # Restricted
    assert result.wavefunction is not None
    assert isinstance(result.wavefunction.scf_eigenvalues_a, ndarray)
    assert isinstance(result.wavefunction.scf_occupations_a, ndarray)
    assert result.wavefunction.scf_eigenvalues_b is None
    assert result.wavefunction.scf_occupations_b is None

    atomic_input_dict["keywords"]["restricted"] = False
    with_wf = AtomicInput(**atomic_input_dict, protocols={"wavefunction": "all"})
    with TCPBClient(settings["tcpb_host"], settings["tcpb_port"]) as TC:
        result = TC.compute(with_wf)

    # B occupations since restricted=False
    assert result.wavefunction is not None
    assert isinstance(result.wavefunction.scf_eigenvalues_a, ndarray)
    assert isinstance(result.wavefunction.scf_occupations_a, ndarray)
    assert isinstance(result.wavefunction.scf_eigenvalues_b, ndarray)
    assert isinstance(result.wavefunction.scf_occupations_b, ndarray)
