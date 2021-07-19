from pathlib import Path
import numpy as np
from time import sleep

from tcpb.models import Mol, JobInput
from tcpb.tcpb import TCProtobufClient


# pytest -k test_model_object_to_job_input_similarity -r P
def test_model_object_to_job_input_similarity(settings, ethylene):
    """
    Test that the new model object function produces the same protobuf
    messages that Stefan's old method created
    """
    # Dicts of options used according to Stefan's old methodology
    stefan_style_options = {
        "method": "hf",
        "basis": "6-31g**",
        "atoms": ethylene["atoms"],
    }
    keywords = {
        # base options
        "precision": "double",
        "convthre": 1e-8,
        "threall": 1e-20,
        # cisno options
        "cisno": "yes",
        "cisnostates": 2,
        "cisnumstates": 2,
        "closed": 7,
        "active": 2,
        "cassinglets": 2,
        "dcimaxiter": 100,
    }
    stefan_style_molecule_keywords = {
        "charge": 0,
        "spinmult": 1,
        "closed_shell": True,
        "restricted": True,
    }
    geom_angstrom = ethylene["geometry"]

    ethylene_mol = Mol(
        atoms = ethylene["atoms"],
        xyz = geom_angstrom,
        units = "Angstrom",
        charge = stefan_style_molecule_keywords["charge"],
        multiplicity = stefan_style_molecule_keywords["spinmult"],
        closed = stefan_style_molecule_keywords["closed_shell"],
        restricted = stefan_style_molecule_keywords["restricted"],
    )
    ethylene_jobinput = JobInput(
        mol = ethylene_mol,
        method_type = "HF",
        run = "energy",
        basis = "6-31g**",
        user_options = keywords,
        # mm_xyz = [],
        # qm_indices = [],
        # prmtop_path = str(Path(__file__).parent / "test_data" / "2water.prmtop"),
    )
    print(ethylene_jobinput.to_pb())
    print()

    # Create protobof JobInput using Stefan's old approach
    client = TCProtobufClient("trash", 65536)
    stefan_style_job_input = client._create_job_input_msg(
        "energy", geom_angstrom, "angstrom", **{**stefan_style_options, **keywords, **stefan_style_molecule_keywords}
    )
    # Create protobuf JobInput using model objects
    model_style_job_input = ethylene_jobinput.to_pb()

    assert model_style_job_input == stefan_style_job_input, "Input error"
    
    client = TCProtobufClient(host=settings["tcpb_host"], port=settings["tcpb_port"])
    client.connect()
    stefan_style_job_output = client.compute_job_sync(
        "energy", geom_angstrom, "angstrom", **{**stefan_style_options, **keywords, **stefan_style_molecule_keywords}
    )
    sleep(0.1) # Make sure terachem cleanup the previous calculation before sending the new one
    model_style_job_output = client.compute_py(ethylene_jobinput)

    print("models.py style:")
    print(model_style_job_output)
    print("\n")
    print("Stefan style:")
    print(stefan_style_job_output)
    print("\n")

    strict_numerical_error = 1e-14
    assert np.linalg.norm(
        np.array(model_style_job_output.charges) - stefan_style_job_output["charges"]
    ) < strict_numerical_error, "Charges different!"
    assert np.linalg.norm(
        np.array(model_style_job_output.spins) - stefan_style_job_output["spins"]
    ) < strict_numerical_error, "Charges different!"
    assert np.abs(
        model_style_job_output.dipole_moment - stefan_style_job_output["dipole_moment"] 
    ) < strict_numerical_error, "Dipole moment different!"
    assert np.linalg.norm(
        np.array(model_style_job_output.dipole_vector) - stefan_style_job_output["dipole_vector"]
    ) < strict_numerical_error, "Dipole vector different!"
    assert np.linalg.norm(
        np.array(model_style_job_output.energy) - stefan_style_job_output["energy"]
    ) < strict_numerical_error, "Energy different!"
    assert np.linalg.norm(
        np.array(model_style_job_output.orb_energies) - stefan_style_job_output["orb_energies"]
    ) < strict_numerical_error, "Orbital energy different!"
    assert np.linalg.norm(
        np.array(model_style_job_output.orb_occupations) - stefan_style_job_output["orb_occupations"]
    ) < strict_numerical_error, "Orbital occupation different!"
    assert np.linalg.norm(
        np.array(model_style_job_output.cas_transition_dipole) - stefan_style_job_output["cas_transition_dipole"]
    ) < strict_numerical_error, "CAS transition dipole different!"
    assert all([i == j for i, j in zip(
        model_style_job_output.cas_energy_labels, stefan_style_job_output["cas_energy_labels"]
    )]), "CAS energy labels different!"
    assert np.linalg.norm(
        np.array(model_style_job_output.bond_order) - stefan_style_job_output["bond_order"].flatten()
    ) < strict_numerical_error, "Bond order different!"

