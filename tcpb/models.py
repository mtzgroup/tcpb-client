import os

from typing import Sequence, List, Dict, Optional

from pydantic import BaseModel, validator, root_validator
from . import terachem_server_pb2 as pb


class Mol(BaseModel):
    atoms: List[str]
    xyz: List[float] # in the order of x1,y1,z1,x2,y2,z2,..., unit must match "units field"
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
    xyz2: List[float] = None
    mm_xyz: List[float] = None # in the order of x1,y1,z1,x2,y2,z2,..., unit must match "units" in "mol" field
    qm_indices: List[int] = None
    prmtop_path: str = None
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
    def xyz2_xyz_length_correct(cls, values):
        """Ensure xyz length is 3x the number of atoms"""
        mol, xyz2 = values.get("mol"), values.get("xyz2")
        if mol is not None and xyz2 is not None and len(xyz2) != len(mol.xyz):
            raise ValueError(
                f"xyz2 of length {len(xyz2)} is not the same as xyz length of {len(mol.xyz)} in mol"
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
    # TODO: Fill out the rest of this data model and each field's associated validator (if required)
    mol: Mol
    # NOTE: This is how you define optional fields
    imd_mmatom_gradient: Optional[List[float]] = None

    @classmethod
    def from_pb(cls, job_output_msg: pb.JobOutput) -> "JobOutput":
        """Create JobOutput object from protocol buffer JobOutput message"""
        # TODO: Fill out method
        return cls(...)