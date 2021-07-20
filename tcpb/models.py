import os
import inspect
import numpy as np

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
    atoms_copy: List[str]
    xyz_copy: List[float] # Length 3 * n_qm of order [i_xyz + 3 * i_qm]

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
    ci_overlap_size: Optional[int]
    ci_overlaps: Optional[List[float]] # Length n_state * n_state
    cis_states: Optional[int]
    cis_unrelaxed_dipoles: Optional[List[float]] # Length 4 * n_state of order [i_xyzd + 4 * i_state]
    cis_relaxed_dipoles: Optional[List[float]] # Length 4 * n_state of order [i_xyzd + 4 * i_state]
    cis_transition_dipoles: Optional[List[float]] # Length 4 * (n_state * (n_state + 1) / 2) of order [i_xyzd + 4 * i_state_2]
    mm_gradient: Optional[List[float]] # Length 3 * n_mm of order [i_xyz + 3 * i_mm]
    molden: Optional[str]

    class Config:
        allow_mutation = False

    # Henry 20210720: The reason we have to use this constructor instead of __init__()
    # is that, __init__ is incompatible with BaseModel, and by overwriting __init__()
    # provided by BaseModel, the default __str__() and __dict__ all fails to work.
    @classmethod
    def from_pb(cls, job_output_msg: pb.JobOutput) -> "JobOutput":
        """Create JobOutput object from protocol buffer JobOutput message"""

        energy = job_output_msg.energy[0] if len(job_output_msg.energy) > 0 else None
        cas_state_number = len(job_output_msg.cas_energy_states) # == 0 if not a cas run
        if cas_state_number > 0:
            energy = job_output_msg.energy[: cas_state_number]
        if job_output_msg.cis_states > 0:
            energy = job_output_msg.energy[: job_output_msg.cis_states + 1]

        output = cls(
            atoms_copy = list(job_output_msg.mol.atoms),
            xyz_copy = list(job_output_msg.mol.xyz),

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
            
            ci_overlap_size = job_output_msg.ci_overlap_size if job_output_msg.ci_overlap_size > 0 else None,
            ci_overlaps = list(job_output_msg.ci_overlaps) if len(job_output_msg.ci_overlaps) > 0 else None,

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

    # Helper function for all other packages depends on tcpb-client before the
    # existence of models.py
    def to_stefan_style_dict(self):
        """
        Creates a results dictionary that mirrors the JobOutput message, using NumPy arrays when appropriate.
        Results are also saved in the prev_results class member.
        An inclusive list of the results members (with types):

        * atoms:              Flat # of atoms NumPy array of 2-character strings
        * geom:               # of atoms by 3 NumPy array of doubles
        * energy:             Either empty, single energy, or flat # of cas_energy_labels of NumPy array of doubles
        * charges:            Flat # of atoms NumPy array of doubles
        * spins:              Flat # of atoms NumPy array of doubles
        * dipole_moment:      Single element (units Debye)
        * dipole_vector:      Flat 3-element NumPy array of doubles (units Debye)
        * job_dir:            String
        * job_scr_dir:        String
        * server_job_id:      Int
        * orbfile:            String (if restricted is True, otherwise not included)
        * orbfile_a:          String (if restricted is False, otherwise not included)
        * orbfile_b:          String (if restricted is False, otherwise not included)
        * orb_energies:       Flat # of orbitals NumPy array of doubles (if restricted is True, otherwise not included)
        * orb_occupations:    Flat # of orbitals NumPy array of doubles (if restricted is True, otherwise not included)
        * orb_energies_a:     Flat # of orbitals NumPy array of doubles (if restricted is False, otherwise not included)
        * orb_occupations_a:  Flat # of orbitals NumPy array of doubles (if restricted is False, otherwise not included)
        * orb_energies_b:     Flat # of orbitals NumPy array of doubles (if restricted is False, otherwise not included)
        * orb_occupations_b:  Flat # of orbitals NumPy array of doubles (if restricted is False, otherwise not included)

        Additional (optional) members of results:

        * bond_order:         # of atoms by # of atoms NumPy array of doubles

        Available per job type:

        * gradient:           # of atoms by 3 NumPy array of doubles (available for 'gradient' job)
        * nacme:              # of atoms by 3 NumPy array of doubles (available for 'coupling' job)
        * ci_overlap:         ci_overlap_size by ci_overlap_size NumPy array of doubles (available for 'ci_vec_overlap' job)

        Available for CAS jobs:

        * cas_energy_labels:  List of tuples of (state, multiplicity) corresponding to the energy list
        * cas_transition_dipole:  Flat 3-element NumPy array of doubles (available for 'coupling' job)

        Available for CIS jobs:

        * cis_states:         Number of excited states for reported properties
        * cis_unrelaxed_dipoles:    # of excited states list of flat 3-element NumPy arrays (default included with 'cis yes', or explicitly with 'cisunrelaxdipole yes', units a.u.)
        * cis_relaxed_dipoles:      # of excited states list of flat 3-element NumPy arrays (included with 'cisrelaxdipole yes', units a.u.)
        * cis_transition_dipoles:   # of excited state combinations (N(N-1)/2) list of flat 3-element NumPy arrays (default includeded with 'cis yes', or explicitly with 'cistransdipole yes', units a.u.)
                                    Order given lexically (e.g. 0->1, 0->2, 1->2 for 2 states)
        """

        result_dict = {
            "atoms": np.array(self.atoms_copy, dtype="S2"),
            "geom": np.array(self.xyz_copy, dtype=np.float64).reshape(-1, 3),
            "charges": np.array(self.charges, dtype=np.float64),
            "spins": np.array(self.spins, dtype=np.float64),
            "dipole_moment": self.dipole_moment,
            "dipole_vector": np.array(self.dipole_vector, dtype=np.float64),
            "job_dir": self.job_dir,
            "job_scr_dir": self.job_scr_dir,
            "server_job_id": self.server_job_id,
        }

        if isinstance(self.orbfile, Tuple):
            result_dict["orbfile_a"] = self.orbfile[0]
            result_dict["orbfile_b"] = self.orbfile[1]
        else:
            result_dict["orbfile"] = self.orbfile
            
        if isinstance(self.orb_energies, Tuple):
            result_dict["orb_energies_a"] = np.array(self.orb_energies[0])
            result_dict["orb_energies_b"] = np.array(self.orb_energies[1])
        else:
            result_dict["orb_energies"] = np.array(self.orb_energies)

        if isinstance(self.orb_occupations, Tuple):
            result_dict["orb_occupations_a"] = np.array(self.orb_occupations[0])
            result_dict["orb_occupations_b"] = np.array(self.orb_occupations[1])
        else:
            result_dict["orb_occupations"] = np.array(self.orb_occupations)

        if self.energy is not None:
            if isinstance(self.energy, List):
                result_dict["energy"] = np.array(self.energy, dtype=np.float64)
            else:
                result_dict["energy"] = self.energy

        if self.gradient is not None:
            result_dict["gradient"] = \
                np.array(self.gradient, dtype=np.float64).reshape(-1, 3)

        if self.nacme is not None:
            result_dict["nacme"] = \
                np.array(self.nacme, dtype=np.float64).reshape(-1, 3)

        if self.cas_transition_dipole is not None:
            result_dict["cas_transition_dipole"] = \
                np.array(self.cas_transition_dipole, dtype=np.float64)

        if self.cas_energy_labels is not None:
            result_dict["cas_energy_labels"] = self.cas_energy_labels

        if self.bond_order is not None:
            nAtoms = len(self.atoms_copy)
            result_dict["bond_order"] = \
                np.array(self.bond_order, dtype=np.float64).reshape(nAtoms, nAtoms)

        if (self.ci_overlap_size is not None) and (self.ci_overlaps is not None):
            print("Henry: in")
            result_dict["ci_overlap"] = \
                np.array(self.ci_overlaps, dtype=np.float64).\
                    reshape(self.ci_overlap_size, self.ci_overlap_size)

        if self.cis_states is not None:
            result_dict["cis_states"] = self.cis_states

        if (self.cis_states is not None) and (self.cis_unrelaxed_dipoles is not None):
            uDips = []
            for i in range(self.cis_states):
                uDips.append(
                    np.array(
                        self.cis_unrelaxed_dipoles[4 * i : 4 * i + 3],
                        dtype=np.float64,
                    )
                )
            result_dict["cis_unrelaxed_dipoles"] = uDips

        if (self.cis_states is not None) and (self.cis_relaxed_dipoles is not None):
            rDips = []
            for i in range(self.cis_states):
                rDips.append(
                    np.array(
                        self.cis_relaxed_dipoles[4 * i : 4 * i + 3],
                        dtype=np.float64,
                    )
                )
            result_dict["cis_relaxed_dipoles"] = rDips

        if (self.cis_states is not None) and (self.cis_transition_dipoles is not None):
            tDips = []
            for i in range((self.cis_states + 1) * self.cis_states / 2):
                tDips.append(
                    np.array(
                        self.cis_transition_dipoles[4 * i : 4 * i + 3],
                        dtype=np.float64,
                    )
                )
            result_dict["cis_transition_dipoles"] = tDips

        if self.molden is not None:
            result_dict["molden"] = self.molden
        
        if self.mm_gradient is not None:
            result_dict["mm_gradient"] = \
                np.array(self.mm_gradient, dtype=np.float64).reshape(-1, 3)

        return result_dict