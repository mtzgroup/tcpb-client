from qcelemental.models import AtomicInput, AtomicResult

from .terachem_server_pb2 import JobInput, JobOutput


def atomic_input_to_job_input(atomic_input: AtomicInput) -> JobInput:
    """Convert AtomicInput to JobInput"""
    pass


def job_output_to_atomic_result(job_output: JobOutput) -> AtomicResult:
    """Convert JobOutput to AtomicResult"""
    pass
