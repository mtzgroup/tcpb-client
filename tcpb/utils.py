from copy import deepcopy

import numpy as np
from google.protobuf.json_format import MessageToDict
from qcio import ProgramInput, SinglePointResults, Structure, Wavefunction, constants

from . import terachem_server_pb2 as pb

SUPPORTED_CALCTYPES = {"ENERGY", "GRADIENT"}


def prog_inp_to_job_inp(prog_inp: ProgramInput) -> pb.JobInput:
    """Convert ProgramInput to JobInput"""
    # Don't mutate original ProgramInput object
    pi_copy = deepcopy(prog_inp)

    # Create Mol instance
    mol_msg = pb.Mol()
    mol_msg.atoms.extend(pi_copy.structure.symbols)
    mol_msg.xyz.extend(pi_copy.structure.geometry.flatten())
    mol_msg.units = pb.Mol.UnitType.BOHR  # Structure always in bohr
    mol_msg.charge = int(pi_copy.structure.charge)
    mol_msg.multiplicity = pi_copy.structure.multiplicity

    # Must remove these keywords from the dictionary so they are not passed to JobInput
    pi_copy.keywords.pop("charge", None)
    pi_copy.keywords.pop("spinmult", None)
    mol_msg.closed = pi_copy.keywords.pop("closed_shell", True)
    mol_msg.restricted = pi_copy.keywords.pop("restricted", True)

    # Create JobInput message
    ji = pb.JobInput(mol=mol_msg)

    # Set calctype
    calctype = pi_copy.calctype.upper()
    if calctype not in SUPPORTED_CALCTYPES:
        raise ValueError(
            f"Calctype '{calctype}' not supported, please select from {SUPPORTED_CALCTYPES}"
        )
    ji.run = pb.JobInput.RunType.Value(calctype)
    # Set Method
    ji.method = pb.JobInput.MethodType.Value(pi_copy.model.method.upper())
    # Set Basis
    ji.basis = pi_copy.model.basis or ""

    # Get keywords that have specific protobuf fields
    ji.return_bond_order = pi_copy.keywords.pop("bond_order", False)
    ji.orb1afile = pi_copy.keywords.pop("orb1afile", "")
    ji.orb1bfile = pi_copy.keywords.pop("orb1bfile", "")

    # Request AO and MO information
    if pi_copy.keywords.pop("mo_output", False):
        ji.imd_orbital_type = pb.JobInput.ImdOrbitalType.WHOLE_C

    # Set all other keywords under the "user_options" catch all
    for key, value in pi_copy.keywords.items():
        ji.user_options.extend([key, str(value)])

    return ji


def mol_to_structure(mol: pb.Mol) -> Structure:
    """Convert mol protobuf message to Structure

    Note:
        Should not use for returning AtomicResults objects because the AtomicResult
        object should be a direct superset of the AtomicInput that created it (and
        already contains the Structure submitted by the user)
    """
    if mol.units == pb.Mol.UnitType.ANGSTROM:
        geom_bohr = np.array(mol.xyz) * constants.ANGSTROM_TO_BOHR
    elif mol.units == pb.Mol.UnitType.BOHR:
        geom_bohr = np.array(mol.xyz)
    else:
        raise ValueError(f"Unknown Unit Type: {mol.units} for molecular geometry")
    return Structure(
        symbols=mol.atoms,
        geometry=geom_bohr,
        charge=mol.charge,
        multiplicity=mol.multiplicity,
    )


def to_single_point_results(job_output: pb.JobOutput) -> SinglePointResults:
    """Create SinglePointResults from JobOutput protobuf message"""
    return SinglePointResults(
        energy=job_output.energy[0],
        gradient=np.array(job_output.gradient),
        scf_dipole_moment=job_output.dipoles[
            :-1
        ],  # Cutting out |D| value; see .proto note re: diples
        calcinfo_natoms=len(job_output.mol.atoms),
        calcinfo_nmo=len(job_output.orba_energies),
        calcinfo_nalpha=int(sum(job_output.orba_occupations)),
        calcinfo_nbeta=int(sum(job_output.orbb_occupations)),
        wavefunction=to_wavefunction_properties(job_output),
    )


def to_wavefunction_properties(
    job_output: pb.JobOutput,
) -> Wavefunction:
    """Extract Wavefunction from JobOutput protobuf message"""
    jo_dict = MessageToDict(job_output, preserving_proto_field_name=True)
    return Wavefunction(
        scf_eigenvalues_a=jo_dict.get("orba_energies"),
        scf_occupations_a=jo_dict.get("orba_occupations"),
        scf_eigenvalues_b=jo_dict.get("orbb_energies", []),
        scf_occupations_b=jo_dict.get("orbb_occupations", []),
    )
