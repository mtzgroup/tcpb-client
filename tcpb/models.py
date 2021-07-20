import os
import inspect

from typing import List, Dict, Tuple, Union, Optional

from pydantic import BaseModel, validator, root_validator
from . import terachem_server_pb2 as pb

from .molden_constructor import tcpb_imd_fields2molden_string


class Mol(BaseModel):
    atoms: List[str]
    xyz: List[float] # Length 3 * n_qm of order [i_xyz + 3 * i_qm], unit must match "units field"
    units: str = "BOHR"
    charge: int = 0
    multiplicity: int = 1
    closed: bool = True
    restricted: bool = True

    class Config:
        validate_assignment = True

    @validator("units")
    def validate_units(cls, v):
        """Validate units"""
        # NOTE: We do not want to write a second data structure, like a dictionary, that
        # contains the keys for valid units. We want a single source of truth for what
        # are valid values and we have that with our protocol buffer messages. We want to
        # leverage those values and methods to create validation at the python level.
        # https://pydantic-docs.helpmanual.io/usage/validators/
        v = v.upper()
        valid_units = pb.Mol.UnitType.keys()
        assert v in valid_units, f"Invalid unit '{v}', valid units are: {valid_units}"
        return v

    @root_validator
    def xyz_atoms_length_correct(cls, values):
        """Ensure xyz length is 3x the number of atoms"""
        atoms, xyz = values.get("atoms"), values.get("xyz")
        if atoms is not None and xyz is not None and len(xyz) != 3 * len(atoms):
            raise ValueError(
                f"xyz of length {len(xyz)} is not 3x atoms length of {len(atoms)}"
            )
        return values

    def to_pb(self) -> pb.Mol:
        """Convert to protocol buffer Mol message"""
        mol_msg = pb.Mol()
        mol_msg.atoms.extend(self.atoms)
        mol_msg.xyz.extend(self.xyz)
        mol_msg.units = pb.Mol.UnitType.Value(self.units)
        mol_msg.charge = self.charge
        mol_msg.multiplicity = self.multiplicity
        mol_msg.closed = self.closed
        mol_msg.restricted = self.restricted

        return mol_msg


class JobInput(BaseModel):
    mol: Mol
    method_type: str
    run: str
    basis: str
    return_bond_order: bool = False
    imd_orbital_type: str = "NO_ORBITAL"
    xyz2: Optional[List[float]] = None
    mm_xyz: Optional[List[float]] = None # Length 3 * n_mm of order [i_xyz + 3 * i_mm], unit must match "units" in "mol" field
    qm_indices: Optional[List[int]] = None
    prmtop_path: Optional[str] = None
    user_options: Dict[str, str] = {}

    class Config:
        validate_assignment = True

    @validator("run")
    def validate_run(cls, v: str):
        """Validate run"""
        # NOTE: See notes above about using the protocol buffers as our single source
        # of truth for valid values and fields. We don't want to create separate
        # dictionaries that define valid values.
        v = v.upper()
        valid_runs = pb.JobInput.RunType.keys()
        assert (
            v in valid_runs
        ), f"Invalid run '{v}', valid run types include: {valid_runs}"
        return v

    @validator("method_type")
    def valid_method_type(cls, v):
        """Validate that the method type is valid for the protocol buffer message"""
        v = v.upper()
        valid_method_types = pb.JobInput.MethodType.keys()
        assert (
            v in valid_method_types
        ), f"Invalid method_type '{v}', valid method types include: {valid_method_types}"
        return v

    @validator("imd_orbital_type")
    def valid_imd_orbital_type(cls, v):
        """Validate that the imd orbital type is valid for the protocol buffer message"""
        v = v.upper()
        valid_imd_orbital_types = pb.JobInput.ImdOrbitalType.keys()
        assert (
            v in valid_imd_orbital_types
        ), f"Invalid imd_orbital_type '{v}', valid imd orbital types include: {valid_imd_orbital_types}"
        return v

    @root_validator
    def xyz2_xyz_length_correct_and_exist_in_ci_vec_overlap(cls, values):
        """Ensure xyz length is 3x the number of atoms"""
        mol = values.get("mol")
        xyz2 = values.get("xyz2")
        run = values.get("run")
        if mol is not None and xyz2 is not None and len(xyz2) != len(mol.xyz):
            raise ValueError(
                f"xyz2 of length {len(xyz2)} is not the same as xyz length of {len(mol.xyz)} in mol"
            )
        if run == "CI_VEC_OVERLAP" and xyz2 is None:
            raise ValueError(
                f"xyz2 is not provided with run = {run}"
            )
        return values

    @root_validator
    def mm_parameters_correct_and_consistent(cls, values):
        """Ensure if one of mm_xyz, qm_indices and prmtop_path exist, then they all exist, and prmtop_path file exist"""
        mm_xyz = values.get("mm_xyz")
        qm_indices = values.get("qm_indices")
        prmtop_path = values.get("prmtop_path")
        if mm_xyz is not None and qm_indices is not None and prmtop_path is not None:
            if os.path.isfile(prmtop_path):
                return values
            else:
                raise ValueError(f"No file is found at prmtop_path {prmtop_path}")
        if mm_xyz is None and qm_indices is None and prmtop_path is None:
            # No QMMM
            return values
        raise ValueError(
            "At least one of mm_xyz, qm_indices and prmtop_path fields is missing for a QMMM job.\n"
            f"mm_xyz = {mm_xyz},\n"
            f"qm_indices = {qm_indices},\n"
            f"prmtop_path = {prmtop_path}\n"
        )

    def to_pb(self) -> pb.JobInput:
        """Return protocol buffer message of JobInput"""
        mol_msg = self.mol.to_pb()
        job_input_msg = pb.JobInput(mol = mol_msg)

        job_input_msg.run = pb.JobInput.RunType.Value(self.run)
        job_input_msg.method = pb.JobInput.MethodType.Value(self.method_type)
        job_input_msg.basis = self.basis
        job_input_msg.return_bond_order = self.return_bond_order
        job_input_msg.imd_orbital_type = pb.JobInput.ImdOrbitalType.Value(self.imd_orbital_type)
        if (self.xyz2 is not None):
            job_input_msg.xyz2.extend(self.xyz2)
        if (self.mm_xyz is not None):
            job_input_msg.mmatom_position.extend(self.mm_xyz)
        if (self.qm_indices is not None):
            job_input_msg.qm_indices.extend(self.qm_indices)
        if (self.prmtop_path is not None):
            job_input_msg.prmtop_path = self.prmtop_path

        for key, value in self.user_options.items():
            job_input_msg.user_options.extend([key, value])
        
        return job_input_msg


class JobOutput(BaseModel):
    charges: List[float] # Length n_qm
    spins: List[float] # Length n_qm
    dipole_moment: float
    dipole_vector: List[float] # Length 3
    job_dir: str
    job_scr_dir: str
    server_job_id: int
    orbfile: Union[str, Tuple[str, str]]
    orb_energies: Union[List[float], Tuple[List[float], List[float]]] # Length n_mo
    orb_occupations: Union[List[float], Tuple[List[float], List[float]]] # Length n_mo

    energy: Optional[Union[float, List[float]]]
    gradient: Optional[List[float]] # Length 3 * n_qm of order [i_xyz + 3 * i_qm]
    nacme: Optional[List[float]] # Length 3 * n_qm of order [i_xyz + 3 * i_qm]
    cas_transition_dipole: Optional[List[float]] # Length 3 * n_transition of order [i_xyz + 3 * i_transition]
    cas_energy_labels: Optional[List[Tuple[int, int]]] # (state, multiplicity), length n_state
    bond_order: Optional[List[float]] # Length n_qm * n_qm
    ci_overlaps: Optional[List[float]] # Length n_state * n_state
    cis_states: Optional[int]
    cis_unrelaxed_dipoles: Optional[List[float]] # Length 4 * n_state of order [i_xyzd + 4 * i_state]
    cis_relaxed_dipoles: Optional[List[float]] # Length 4 * n_state of order [i_xyzd + 4 * i_state]
    cis_transition_dipoles: Optional[List[float]] # Length 4 * (n_state * (n_state + 1) / 2) of order [i_xyzd + 4 * i_state_2]
    mm_gradient: Optional[List[float]] # Length 3 * n_mm of order [i_xyz + 3 * i_mm]
    molden: Optional[str]

    class Config:
        allow_mutation = False

    @classmethod
    def from_pb(cls, job_output_msg: pb.JobOutput) -> "JobOutput":
        """Create JobOutput object from protocol buffer JobOutput message"""

        energy = job_output_msg.energy[0]
        cas_state_number = len(job_output_msg.cas_energy_states) # == 0 if not a cas run
        if cas_state_number > 0:
            energy = job_output_msg.energy[: cas_state_number]
        if job_output_msg.cis_states > 0:
            energy = job_output_msg.energy[: job_output_msg.cis_states + 1]

        output = cls(
            charges = list(job_output_msg.charges),
            spins = list(job_output_msg.spins),
            dipole_moment = job_output_msg.dipoles[3],
            dipole_vector = list(job_output_msg.dipoles[:3]),
            job_dir = job_output_msg.job_dir,
            job_scr_dir = job_output_msg.job_scr_dir,
            server_job_id = job_output_msg.server_job_id,

            orbfile = job_output_msg.orb1afile
                if job_output_msg.mol.closed else (job_output_msg.orb1afile, job_output_msg.orb1bfile),
            orb_energies = list(job_output_msg.orba_energies)
                if job_output_msg.mol.closed else (list(job_output_msg.orba_energies), list(job_output_msg.orbb_energies)),
            orb_occupations = list(job_output_msg.orba_occupations)
                if job_output_msg.mol.closed else (list(job_output_msg.orba_occupations), list(job_output_msg.orbb_occupations)),

            energy = energy,
            gradient = list(job_output_msg.gradient) if len(job_output_msg.gradient) > 0 else None,
            nacme = list(job_output_msg.nacme) if len(job_output_msg.nacme) > 0 else None,
            cas_transition_dipole = list(job_output_msg.cas_transition_dipole) if len(job_output_msg.cas_transition_dipole) > 0 else None,
            cas_energy_labels = list(zip(
                    job_output_msg.cas_energy_states,
                    job_output_msg.cas_energy_mults,
                )) if cas_state_number > 0 else None,

            bond_order = list(job_output_msg.bond_order) if len(job_output_msg.bond_order) > 0 else None,
            ci_overlap = list(job_output_msg.ci_overlaps) if len(job_output_msg.ci_overlaps) > 0 else None,

            cis_states = job_output_msg.cis_states if job_output_msg.cis_states > 0 else None,
            cis_unrelaxed_dipoles = list(job_output_msg.cis_unrelaxed_dipoles)
                if job_output_msg.cis_states > 0 and len(job_output_msg.cis_unrelaxed_dipoles) > 0 else None,
            cis_relaxed_dipoles = list(job_output_msg.cis_relaxed_dipoles)
                if job_output_msg.cis_states > 0 and len(job_output_msg.cis_relaxed_dipoles) > 0 else None,
            cis_transition_dipoles = list(job_output_msg.cis_transition_dipoles)
                if job_output_msg.cis_states > 0 and len(job_output_msg.cis_transition_dipoles) > 0 else None,

            mm_gradient = list(job_output_msg.mmatom_gradient) if len(job_output_msg.mmatom_gradient) > 0 else None,
            molden = tcpb_imd_fields2molden_string(job_output_msg) if len(job_output_msg.compressed_mo_vector) > 0 else None,
        )
        return output

    # def __init__(self, job_output_msg: pb.JobOutput):
    #     """Create JobOutput object from protocol buffer JobOutput message"""
    #     self.charges = job_output_msg.charges
    #     self.spins = job_output_msg.spins
    #     self.dipole_moment = job_output_msg.dipoles[3]
    #     self.dipole_vector = job_output_msg.dipoles[:3]
    #     self.job_dir = job_output_msg.job_dir
    #     self.job_scr_dir = job_output_msg.job_scr_dir
    #     self.server_job_id = job_output_msg.server_job_id

    #     self.energy = job_output_msg.energy[0] # The energies for multiple states are set later

    #     if job_output_msg.mol.closed is True:
    #         self.orbfile = job_output_msg.orb1afile
    #         self.orb_energies = job_output_msg.orba_energies
    #         self.orb_occupations = job_output_msg.orba_occupations
    #     else:
    #         self.orbfile = (job_output_msg.orb1afile, job_output_msg.orb1bfile)
    #         self.orb_energies = (job_output_msg.orba_energies, job_output_msg.orbb_energies)
    #         self.orb_occupations = (job_output_msg.orba_occupations, job_output_msg.orbb_occupations)

    #     if len(job_output_msg.gradient):
    #         self.gradient = job_output_msg.gradient

    #     if len(job_output_msg.nacme):
    #         self.nacme = job_output_msg.nacme

    #     if len(job_output_msg.cas_transition_dipole):
    #         self.cas_transition_dipole = job_output_msg.cas_transition_dipole

    #     cas_state_number = len(job_output_msg.cas_energy_states) # == 0 if not a cas run
    #     if cas_state_number:
    #         self.energy = job_output_msg.energy[: cas_state_number]
    #         self.cas_energy_labels = list(zip(
    #             job_output_msg.cas_energy_states,
    #             job_output_msg.cas_energy_mults,
    #         ))

    #     if len(job_output_msg.bond_order):
    #         self.bond_order = job_output_msg.bond_order

    #     if len(job_output_msg.ci_overlaps):
    #         self.ci_overlap = job_output_msg.ci_overlaps

    #     if job_output_msg.cis_states > 0:
    #         self.energy = job_output_msg.energy[: job_output_msg.cis_states + 1]
    #         self.cis_states = job_output_msg.cis_states

    #         if len(job_output_msg.cis_unrelaxed_dipoles):
    #             self.cis_unrelaxed_dipoles = job_output_msg.cis_unrelaxed_dipoles
    #         if len(job_output_msg.cis_relaxed_dipoles):
    #             self.cis_relaxed_dipoles = job_output_msg.cis_relaxed_dipoles
    #         if len(job_output_msg.cis_transition_dipoles):
    #             self.cis_transition_dipoles = job_output_msg.cis_transition_dipoles

    #     if len(job_output_msg.mmatom_gradient):
    #         self.mm_gradient = job_output_msg.mmatom_gradient
    
    #     if len(job_output_msg.compressed_mo_vector):
    #         self.molden = tcpb_imd_fields2molden_string(job_output_msg)

    # def __str__(self):
    #     attributes = inspect.getmembers(type(self), lambda a : not(inspect.isroutine(a)))
    #     attributes = [a for a in attributes if not(a[0].startswith('_'))]
    #     attributes = dict(attributes)

    #     return str(attributes)