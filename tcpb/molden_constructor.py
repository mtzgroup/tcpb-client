import numpy as np

"""Helper function to convert IMD AO and MO fields to molden file format.
"""

"""Extract imd and related fields and construct the content of molden file
Args:
    job_output: the protobuf job_output object
    return: a string containing the content of a molden file
"""


def tcpb_imd_fields2molden_string(job_output):
    try:
        atoms = job_output.mol.atoms
        xyz = np.array(job_output.mol.xyz, dtype=np.float32)
        compressed_ao_data = np.array(job_output.compressed_ao_data, dtype=np.int32)
        compressed_mo_vector = np.array(
            job_output.compressed_mo_vector, dtype=np.float32
        )
        compressed_primitive_data = np.array(
            job_output.compressed_primitive_data, dtype=np.float32
        )
        orba_energies = np.array(job_output.orba_energies, dtype=np.float32)
        orbb_energies = np.array(job_output.orbb_energies, dtype=np.float32)
        orba_occupations = np.array(job_output.orba_occupations, dtype=np.float32)
        orbb_occupations = np.array(job_output.orbb_occupations, dtype=np.float32)

        restricted = job_output.mol.restricted
        # NOTE: Commented out because unused; preserving for now...
        # unit_if_au = job_output.mol.units == pb.Mol.UnitType.Value("BOHR")
        n_atom = len(atoms)
        n_AO = np.size(compressed_ao_data) // 3

    except AttributeError:
        # raise Exception("An unsupported version of client interface (proto file) is used.");
        return None

    # constants
    bohr2angstrom = 0.52917724924
    element_name2atomic_number = {
        "H": 1,
        "D": 1,
        "He": 2,
        "Li": 3,
        "Be": 4,
        "B": 5,
        "C": 6,
        "N": 7,
        "O": 8,
        "F": 9,
        "Ne": 10,
        "Na": 11,
        "Mg": 12,
        "Al": 13,
        "Si": 14,
        "P": 15,
        "S": 16,
        "Cl": 17,
        "Ar": 18,
        "K": 19,
        "Ca": 20,
        "Sc": 21,
        "Ti": 22,
        "V": 23,
        "Cr": 24,
        "Mn": 25,
        "Fe": 26,
        "Co": 27,
        "Ni": 28,
        "Cu": 29,
        "Zn": 30,
        "Ga": 31,
        "Ge": 32,
        "As": 33,
        "Se": 34,
        "Br": 35,
        "Kr": 36,
        "Rb": 37,
        "Sr": 38,
        "Y": 39,
        "Zr": 40,
        "Nb": 41,
        "Mo": 42,
        "Tc": 43,
        "Ru": 44,
        "Rh": 45,
        "Pd": 46,
        "Ag": 47,
        "Cd": 48,
        "In": 49,
        "Sn": 50,
        "Sb": 51,
        "Te": 52,
        "I": 53,
        "Xe": 54,
        "Cs": 55,
        "Ba": 56,
        "La": 57,
        "Ce": 58,
        "Pr": 59,
        "Nd": 60,
        "Pm": 61,
        "Sm": 62,
        "Eu": 63,
        "Gd": 64,
        "Tb": 65,
        "Dy": 66,
        "Ho": 67,
        "Er": 68,
        "Tm": 69,
        "Yb": 70,
        "Lu": 71,
        "Hf": 72,
        "Ta": 73,
        "W": 74,
        "Re": 75,
        "Os": 76,
        "Ir": 77,
        "Pt": 78,
        "Au": 79,
        "Hg": 80,
        "Tl": 81,
        "Pb": 82,
        "Bi": 83,
        "Po": 84,
        "At": 85,
        "Rn": 86,
        "Fr": 87,
        "Ra": 88,
        "Ac": 89,
        "Th": 90,
        "Pa": 91,
        "U": 92,
        "Np": 93,
        "Pu": 94,
        "Am": 95,
        "Cm": 96,
        "Bk": 97,
        "Cf": 98,
        "Es": 99,
        "Fm": 100,
        "Md": 101,
        "No": 102,
        "Lr": 103,
        "Rf": 104,
        "Db": 105,
        "Sg": 106,
        "Bh": 107,
        "Hs": 108,
        "Mt": 109,
        "Ds": 110,
        "Rg": 111,
        "Cn": 112,
        "Nh": 113,
        "Fl": 114,
        "Mc": 115,
        "Lv": 116,
        "Ts": 117,
        "Og": 118,
    }
    N_FLOAT_PER_BASIS_COMPRESSED = 3
    N_FLOAT_PER_PRIMITIVE = 2

    # construction
    text = "[Molden Format]\n[Title]\nWritten by TeraChem\n[Atoms] Angs\n"

    for i_atom in range(n_atom):
        text += (
            atoms[i_atom]
            + "   "
            + str(i_atom + 1)
            + "   "
            + str(element_name2atomic_number[atoms[i_atom]])
            + " "
            + "%10.5f %10.5f %10.5f"
            % (
                xyz[i_atom * 3 + 0] * bohr2angstrom,
                xyz[i_atom * 3 + 1] * bohr2angstrom,
                xyz[i_atom * 3 + 2] * bohr2angstrom,
            )
            + "\n"
        )

    text += "[GTO]\n"
    i_atom = -1
    n_total_primitive = 0
    for i_ao in range(n_AO):
        if i_atom != compressed_ao_data[i_ao * N_FLOAT_PER_BASIS_COMPRESSED + 2]:
            if i_atom != -1:
                text += "\n"
                # additional line after each atom complete
            i_atom = compressed_ao_data[i_ao * N_FLOAT_PER_BASIS_COMPRESSED + 2]
            text += "    " + str(i_atom + 1) + " 0\n"

        n_primitive = compressed_ao_data[i_ao * N_FLOAT_PER_BASIS_COMPRESSED + 1]
        if_print_primitive = True
        if (
            compressed_ao_data[i_ao * N_FLOAT_PER_BASIS_COMPRESSED + 0]
            == 1 << (0 * 2) + 0
        ):
            text += " s    " + str(n_primitive) + " 1.00\n"
        elif (
            compressed_ao_data[i_ao * N_FLOAT_PER_BASIS_COMPRESSED + 0]
            == 1 << (1 * 2) + 0
        ):
            text += " p    " + str(n_primitive) + " 1.00\n"
        elif (
            compressed_ao_data[i_ao * N_FLOAT_PER_BASIS_COMPRESSED + 0]
            == 1 << (2 * 2) + 0
        ):
            text += " d    " + str(n_primitive) + " 1.00\n"
        else:
            if_print_primitive = False

        if if_print_primitive:
            for i_primitive in range(n_primitive):
                text += (
                    "        "
                    + "%10.6f"
                    % (
                        compressed_primitive_data[
                            (n_total_primitive + i_primitive) * N_FLOAT_PER_PRIMITIVE
                            + 0
                        ]
                    )
                    + "        "
                    + "%10.6f"
                    % (
                        compressed_primitive_data[
                            (n_total_primitive + i_primitive) * N_FLOAT_PER_PRIMITIVE
                            + 1
                        ]
                    )
                    + "\n"
                )

        n_total_primitive += n_primitive

    text += "[MO]\n"
    for i_ao in range(n_AO):
        text += (
            " Ene= %10.4f\n" % (orba_energies[i_ao])
            + " Spin= Alpha\n"
            + " Occup= %3.1f\n" % (orba_occupations[i_ao])
        )
        for j_ao in range(n_AO):
            text += " %4d %10.5f\n" % (
                j_ao + 1,
                compressed_mo_vector[i_ao * n_AO + j_ao],
            )
    if not restricted:
        for i_ao in range(n_AO):
            text += (
                " Ene= %10.4f\n" % (orbb_energies[i_ao])
                + " Spin= Alpha\n"
                + " Occup= %3.1f\n" % (orbb_occupations[i_ao])
            )
            for j_ao in range(n_AO):
                text += " %4d %10.5f\n" % (
                    j_ao + 1,
                    compressed_mo_vector[n_AO * n_AO + i_ao * n_AO + j_ao],
                )

    return text
