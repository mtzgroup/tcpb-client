from qcelemental.models import AtomicInput, AtomicResult

from .terachem_server_pb2 import JobInput, JobOutput, Mol


def atomic_input_to_job_input(atomic_input: AtomicInput) -> JobInput:
    """Convert AtomicInput to JobInput"""
    # Create Mol instance
    mol_msg = Mol()
    mol_msg.atoms.extend(atomic_input.molecule.symbols)
    mol_msg.xyz.extend(atomic_input.molecule.geometry.flatten())
    mol_msg.units = Mol.UnitType.BOHR  # Molecule always in bohr
    mol_msg.charge = int(atomic_input.molecule.molecular_charge)
    mol_msg.multiplicity = atomic_input.molecule.molecular_multiplicity
    mol_msg.closed = atomic_input.keywords.pop("closed_shell", True)
    mol_msg.restricted = atomic_input.keywords.pop("restricted", True)

    # Create Job Inputs
    ji = JobInput(mol=mol_msg)
    try:
        ji.run = getattr(JobInput.RunType, atomic_input.driver.upper())
    except AttributeError:
        raise ValueError(f"Driver '{atomic_input.driver}' not supported by TCPB.")

    try:
        ji.method = getattr(JobInput.MethodType, atomic_input.model.method.upper())
    except AttributeError:
        raise ValueError(f"Method '{atomic_input.model.method}' not supported by TCPB.")

    ji.basis = atomic_input.model.basis
    ji.return_bond_order = atomic_input.keywords.pop("bond_order", False)
    # Drop keyword terms already applied to Molecule
    atomic_input.keywords.pop("charge", None)
    atomic_input.keywords.pop("spinmult", None)

    for key, value in atomic_input.keywords.items():
        ji.user_options.extend([key, str(value)])

    return ji


def job_output_to_atomic_result(job_output: JobOutput) -> AtomicResult:
    """Convert JobOutput to AtomicResult"""
    pass
