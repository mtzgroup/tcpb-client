from pathlib import Path
import numpy as np

from tcpb.models import Mol, JobInput
from tcpb.tcpb import TCProtobufClient


# pytest -k test_model_object_to_job_input_similarity -r P
def test_model_object_to_job_input_similarity(ethylene):
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
    client = TCProtobufClient("host", 11111)
    stefan_style_jobinput = client._create_job_input_msg(
        "energy", geom_angstrom, "angstrom", **{**stefan_style_options, **keywords, **stefan_style_molecule_keywords}
    )
    # Create protobuf JobInput using model objects
    model_style_job_input = ethylene_jobinput.to_pb()

    # print("Stefan style:")
    # print(stefan_style_jobinput)
    # print()
    # print("models.py style:")
    # print(model_style_job_input)

    assert model_style_job_input == stefan_style_jobinput
