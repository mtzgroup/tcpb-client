from numpy import array
from qcelemental.models import AtomicInput, AtomicResult, Molecule
from qcelemental import Datum
from qcelemental.models.results import AtomicResultProperties, Provenance

from . import terachem_server_pb2 as pb


def atomic_input_to_job_input(atomic_input: AtomicInput) -> pb.JobInput:
    """Convert AtomicInput to JobInput"""
    # Create Mol instance
    mol_msg = pb.Mol()
    mol_msg.atoms.extend(atomic_input.molecule.symbols)
    mol_msg.xyz.extend(atomic_input.molecule.geometry.flatten())
    mol_msg.units = pb.Mol.UnitType.BOHR  # Molecule always in bohr
    mol_msg.charge = int(atomic_input.molecule.molecular_charge)
    mol_msg.multiplicity = atomic_input.molecule.molecular_multiplicity
    mol_msg.closed = atomic_input.keywords.pop("closed_shell", True)
    mol_msg.restricted = atomic_input.keywords.pop("restricted", True)

    # Create Job Inputs
    ji = pb.JobInput(mol=mol_msg)
    try:
        ji.run = getattr(pb.JobInput.RunType, atomic_input.driver.upper())
    except AttributeError:
        raise ValueError(f"Driver '{atomic_input.driver}' not supported by TCPB.")

    try:
        ji.method = getattr(pb.JobInput.MethodType, atomic_input.model.method.upper())
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


def mol_to_molecule(mol: pb.Mol) -> Molecule:
    """Convert mol protobuf message to Molecule"""
    if mol.units == pb.Mol.UnitType.ANGSTROM:
        geom_angstrom = Datum("geometry", "angstrom", array(mol.xyz))
        geom_bohr = geom_angstrom.to_units("bohr")
    elif mol.units == pb.Mol.UnitType.BOHR:
        geom_bohr = list(mol.xyz)
    else:
        raise ValueError(f"Unknown Unit Type: {mol.units} for molecular geometry")
    return Molecule(
        symbols=mol.atoms,
        geometry=geom_bohr,
        molecular_multiplicity=mol.multiplicity,
    )


def job_output_to_atomic_result(
    *, atomic_input: AtomicInput, job_output: pb.JobOutput
) -> AtomicResult:
    """Convert JobOutput to AtomicResult"""
    if atomic_input.driver == "energy":
        # Select first element in list (ground state); may need to modify for excited
        # state
        return_result = job_output.energy[0]

    elif atomic_input.driver == "gradient":
        return_result = job_output.gradient

    else:
        raise ValueError(f"Unsupported driver: {atomic_input.driver}")

    atomic_result = AtomicResult(
        molecule=mol_to_molecule(job_output.mol),
        driver=atomic_input.driver,
        model=atomic_input.model,
        keywords=atomic_input.keywords,
        return_result=return_result,
        provenance=Provenance(
            creator="TeraChem Protobuf Server",
            version="1.9-2021.01-dev",
            routine="terachem -s",
        ),
        properties=job_output_to_atomic_result_properties(job_output),
        success=True,
        extras={
            "qcvars": {
                "charges": job_output.charges,
                "spins": job_output.spins,
                "job_dir": job_output.job_dir,
                "job_scr_dir": job_output.job_scr_dir,
                "server_job_id": job_output.server_job_id,
                "orb1afile": job_output.orb1afile,
                "orb1bfile": job_output.orb1bfile,
                "bond_order": job_output.bond_order,
                "orba_energies": job_output.orba_energies,
                "orba_occupations": job_output.orba_occupations,
                "orbb_energies": job_output.orbb_energies,
                "orbb_occupations": job_output.orbb_occupations,
            }
        },
    )
    return atomic_result


def job_output_to_atomic_result_properties(
    job_output: pb.JobOutput,
) -> AtomicResultProperties:
    """Convert a JobOutput protobuf message to MolSSI QCSchema AtomicResultProperties"""
    return AtomicResultProperties(
        return_energy=job_output.energy[0],
        scf_dipole_moment=job_output.dipoles[
            :-1
        ],  # Cutting out |D| value; see .proto note re: diples
        calcinfo_natom=len(job_output.mol.atoms),
    )