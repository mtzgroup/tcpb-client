from typing import Any, Dict

from google.protobuf.json_format import MessageToDict
from numpy import array
from qcelemental import Datum
from qcelemental.models import AtomicInput, BasisSet, Molecule
from qcelemental.models.results import AtomicResultProperties, WavefunctionProperties

from . import terachem_server_pb2 as pb
from .config import TCFEKeywords

SUPPORTED_DRIVERS = {"ENERGY", "GRADIENT"}


def atomic_input_to_job_input(atomic_input: AtomicInput) -> pb.JobInput:
    """Convert AtomicInput to JobInput"""
    # Don't mutate original atomic_input object
    ai_copy = atomic_input.copy(deep=True)

    # Create Mol instance
    mol_msg = pb.Mol()
    mol_msg.atoms.extend(ai_copy.molecule.symbols)
    mol_msg.xyz.extend(ai_copy.molecule.geometry.flatten())
    mol_msg.units = pb.Mol.UnitType.BOHR  # Molecule always in bohr
    mol_msg.charge = int(ai_copy.molecule.molecular_charge)
    mol_msg.multiplicity = ai_copy.molecule.molecular_multiplicity
    mol_msg.closed = ai_copy.keywords.pop("closed_shell", True)
    mol_msg.restricted = ai_copy.keywords.pop("restricted", True)
    # Drop keyword terms already applied from Molecule object
    ai_copy.keywords.pop("charge", None)  # mol_msg.charge
    ai_copy.keywords.pop("spinmult", None)  # mol_msg.multiplicity

    # Create JobInput message
    ji = pb.JobInput(mol=mol_msg)
    # Set driver
    driver = ai_copy.driver.upper()
    if driver not in SUPPORTED_DRIVERS:
        # Only support QCEngine supported drivers; energy, gradient, hessian, properties
        raise ValueError(
            f"Driver '{driver}' not supported, please select from {SUPPORTED_DRIVERS}"
        )
    ji.run = pb.JobInput.RunType.Value(driver)
    # Set Method
    ji.method = pb.JobInput.MethodType.Value(ai_copy.model.method.upper())
    # Set Basis
    ji.basis = ai_copy.model.basis

    # Get keywords that have specific protobuf fields
    ji.return_bond_order = ai_copy.keywords.pop("bond_order", False)
    ji.orb1afile = ai_copy.keywords.pop("orb1afile", "")
    ji.orb1bfile = ai_copy.keywords.pop("orb1bfile", "")

    # Request AO and MO information
    if ai_copy.keywords.pop("mo_output", False):
        ji.imd_orbital_type = pb.JobInput.ImdOrbitalType.WHOLE_C

    # Set all other keywords under the "user_options" catch all
    for key, value in ai_copy.keywords.items():
        ji.user_options.extend([key, str(value)])

    return ji


def mol_to_molecule(mol: pb.Mol) -> Molecule:
    """Convert mol protobuf message to Molecule

    Note:
        Should not use for returning AtomicResults objects because the AtomicResult
        object should be a direct superset of the AtomicInput that created it (and
        already contains the Molecule submitted by the user)
    """
    if mol.units == pb.Mol.UnitType.ANGSTROM:
        geom_angstrom = Datum("geometry", "angstrom", array(mol.xyz))
        geom_bohr = geom_angstrom.to_units("bohr")
    elif mol.units == pb.Mol.UnitType.BOHR:
        geom_bohr = array(mol.xyz)
    else:
        raise ValueError(f"Unknown Unit Type: {mol.units} for molecular geometry")
    return Molecule(
        symbols=mol.atoms,
        geometry=geom_bohr,
        molecular_multiplicity=mol.multiplicity,
    )


# def job_output_to_atomic_result(
#     *,
#     atomic_input: AtomicInput,
#     job_output: pb.JobOutput,
#     creator: str,
# ) -> AtomicResult:
#     """Convert JobOutput to AtomicResult"""
#     # Convert job_output to python types
#     # NOTE: Required so that AtomicResult is JSON serializable. Protobuf types are not.
#     jo_dict = MessageToDict(job_output, preserving_proto_field_name=True)

#     if atomic_input.driver.upper() == "ENERGY":
#         # Select first element in list (ground state); may need to modify for excited
#         # states
#         return_result: Union[float, List[float]] = jo_dict["energy"][0]

#     elif atomic_input.driver.upper() == "GRADIENT":
#         return_result = jo_dict["gradient"]

#     else:
#         raise ValueError(
#             f"Unsupported driver: {atomic_input.driver.upper()}, supported drivers "
#             f"include: {SUPPORTED_DRIVERS}"
#         )

#     # Prepare AtomicInput to be base input for AtomicResult
#     atomic_input_dict = atomic_input.dict()
#     atomic_input_dict.pop("provenance", None)

#     # Create AtomicResult as superset of AtomicInput values
#     atomic_result = AtomicResult(
#         **atomic_input_dict,
#         # Create new provenance object
#         provenance=Provenance(
#             creator=creator,
#             version="",
#             routine="tcpb.TCProtobufClient | TCFrontEndClient.compute",
#         ),
#         return_result=return_result,
#         properties=to_atomic_result_properties(job_output),
#         # NOTE: Wavefunction will only be added if atomic_input.protocols.wavefunction != 'none'
#         wavefunction=to_wavefunction_properties(job_output, atomic_input),
#         success=True,
#     )
#     # And extend extras to include values additional to input extras
#     atomic_result.extras.update(
#         {
#             settings.extras_qcvars_kwarg: {
#                 "charges": jo_dict.get("charges"),
#                 "spins": jo_dict.get("spins"),
#                 "meyer_bond_order": jo_dict.get("bond_order"),
#                 "orb_size": jo_dict.get("orb_size"),
#                 "excited_state_energies": jo_dict.get("energy"),
#                 "cis_transition_dipoles": jo_dict.get("cis_transition_dipoles"),
#                 "compressed_bond_order": jo_dict.get("compressed_bond_order"),
#                 "compressed_hessian": jo_dict.get("compressed_hessian"),
#                 "compressed_ao_data": jo_dict.get("compressed_ao_data"),
#                 "compressed_primitive_data": jo_dict.get("compressed_primitive_data"),
#                 "compressed_mo_vector": jo_dict.get("compressed_mo_vector"),
#                 "imd_mmatom_gradient": jo_dict.get("imd_mmatom_gradient"),
#             },
#             settings.extras_job_kwarg: {
#                 "job_dir": jo_dict.get("job_dir"),
#                 "job_scr_dir": jo_dict.get("job_scr_dir"),
#                 "server_job_id": jo_dict.get("server_job_id"),
#                 "orb1afile": jo_dict.get("orb1afile"),
#                 "orb1bfile": jo_dict.get("orb1bfile"),
#             },
#         }
#     )
#     return atomic_result


def to_atomic_result_properties(job_output: pb.JobOutput) -> AtomicResultProperties:
    """Extract AtomicResultProperties from JobOutput protobuf message"""
    return AtomicResultProperties(
        return_energy=job_output.energy[0],
        scf_dipole_moment=job_output.dipoles[
            :-1
        ],  # Cutting out |D| value; see .proto note re: diples
        calcinfo_natom=len(job_output.mol.atoms),
        calcinfo_nmo=len(job_output.orba_energies),
        calcinfo_nalpha=sum(job_output.orba_occupations),
        calcinfo_nbeta=sum(job_output.orbb_occupations),
    )


def to_wavefunction_properties(
    job_output: pb.JobOutput, atomic_input: AtomicInput
) -> WavefunctionProperties:
    """Extract WavefunctionProperties from JobOutput protobuf message"""
    jo_dict = MessageToDict(job_output, preserving_proto_field_name=True)
    return WavefunctionProperties(
        basis=BasisSet(
            name=atomic_input.model.basis,
            center_data={},  # TODO: need to fill out
            atom_map=[],  # TODO: need to fill out
        ),
        restricted=atomic_input.keywords.get("restricted", True),
        scf_eigenvalues_a=jo_dict.get("orba_energies"),
        scf_occupations_a=jo_dict.get("orba_occupations"),
        scf_eigenvalues_b=jo_dict.get("orbb_energies", []),
        scf_occupations_b=jo_dict.get("orbb_occupations", []),
    )


def _validate_tcfe_keywords(tcfe_keywords: Dict[str, Any]) -> None:
    """Validates tcfe:keywords"""
    for key in tcfe_keywords.keys():
        TCFEKeywords(key)
