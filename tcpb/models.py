from typing import List, Optional

from pydantic import BaseModel, validator, root_validator
from . import terachem_server_pb2 as pb


class Mol(BaseModel):
    atoms: List[str]
    xyz: List[float]
    units: str
    charge: int
    multiplicity: int
    closed: bool
    restricted: bool

    @validator("units")
    def validate_units(cls, v):
        """Validate units"""
        # NOTE: We do not want to write a second data structure, like a dictionary, that
        # contains the keys for valid units. We want a single source of truth for what
        # are valid values and we have that with our protocol buffer messages. We want to
        # leverage those values and methods to create validation at the python level.
        # https://pydantic-docs.helpmanual.io/usage/validators/
        v = v.lower()
        valid_units = pb.Mol.UnitType.keys()
        assert v in valid_units, f"Invalid unit '{v}', valid units are: {valid_units}"
        return v

    @root_validator
    def xyz_atoms_length_correct(cls, values):
        """Ensure xyz length is 3x the number of atoms"""
        # NOTE: This is how you write a validator that operates on the entire data
        # structure requiring multiple values to guarantee correctness
        # https://pydantic-docs.helpmanual.io/usage/validators/#root-validators
        atoms, xyz = values.get("atoms"), values.get("xyz")
        if atoms is not None and xyz is not None and len(xyz) != 3 * len(atoms):
            raise ValueError(
                f"xyz of length {len(xyz)} is not 3x atoms length of {len(atoms)}"
            )
        return values

    def to_pb(self) -> pb.Mol:
        """Convert to protocol buffer Mol message"""
        # TODO: Fill out method. Use the protocol buffer methods to convert data to
        # their corresponding types without hard-coding values that will require
        # updating when we update the protocol buffer interface. Again, we want to use
        # the protocol buffer's methods and definitions as our single source of truth
        mol = pb.Mol()
        # Example of what I mean above
        mol.units = pb.Mol.UnitType.Value(self.units)
        # TODO: Keep filling out method
        return mol


class JobInput(BaseModel):
    # TODO: Fill out the rest of this data model and each field's associated validator (if required)
    mol: Mol
    method_type: str
    run: str

    @validator("run")
    def validate_run(cls, v) -> str:
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
    def valid_method_type(cls, v) -> str:
        """Validate that the method type is valid for the protocol buffer message"""
        v = v.upper()
        valid_method_types = pb.JobInput.MethodType.keys()
        assert (
            v in valid_method_types
        ), f"Invalid method_type, valid method types include: {valid_method_types}"
        return v

    def to_pb(self) -> pb.JobInput:
        """Return protocol buffer message of JobInput"""
        # TODO: Fill out method. Use the protocol buffer methods to convert data to
        # their corresponding types without hard-coding values that will require
        # updating when we update the protocol buffer interface
        mol = self.mol.to_pb()
        job_input_msg = pb.JobInput(mol=mol)
        # Example of what I mean above
        job_input_msg.run = pb.JobInput.RunType.Value(self.run)
        # TODO: Keep filling out method
        return job_input_msg

    @classmethod
    def coupling_input(cls, value1, value2, etc) -> "JobInput":
        """Convenience method for creating a coupling computation"""
        # NOTE: Convenience methods to quickly instantiate a JobInput for a certain
        # job type, if you want them to exist, should be @classmethod functions like
        # this.
        return cls(...)


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