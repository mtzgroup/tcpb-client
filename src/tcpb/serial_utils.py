from __future__ import absolute_import, division, print_function

"""Some small utilities for handling TeraChem serialized files
"""

import numpy as np


def read_orbfile(orbfile, num_rows, num_cols):
    """Deserialize a TeraChem binary orbital file of doubles.

    HF/DFT orbitals (which are stored column-major for TeraChem) are transposed on deserialization.

    Args:
        orbfile: Filename of orbital file to read
        num_rows: Rows in MO coefficient matrix
        num_cols: Columns in MO coefficient matrix

    Returns:
        (num_rows, num_cols): NumPy array of MO coefficients
    """
    orbs = np.fromfile(orbfile, dtype=np.float64)

    orbs = orbs.reshape((num_rows, num_cols))

    if orbfile.endswith("c0") or orbfile.endswith("ca0") or orbfile.endswith("cb0"):
        orbs = orbs.transpose()

    return orbs


def write_orbfile(orbs, orbfile):
    """Serialize a TeraChem binary orbital file of doubles.

    HF/DFT orbitals (which are stored column-major for TeraChem) are transposed on serialization.

    Args:
        orbs: Non-flat NumPy array of MO coefficients
        orbfile: Filename of orbital file to write
    """
    if not isinstance(orbs, np.ndarray) or len(orbs.shape) != 2:
        raise SyntaxError(
            "Need a shaped NumPy array for write_orbfile to do proper serialization for TeraChem."
        )

    if orbfile.endswith("c0") or orbfile.endswith("ca0") or orbfile.endswith("cb0"):
        orbs = orbs.transpose()

    orbs.astype(np.float64).tofile(orbfile)


def read_ci_vector(cvecfile, num_rows, num_cols):
    """Deserialize a TeraChem binary CI vector file of doubles.

    Args:
        cvecfile: Filename of CI vector file to read
        num_rows: Rows in CI vector
        num_cols: Columns in CI vector matrix
    Returns a (num_rows, num_cols) NumPy array of MO coefficients
    """
    ci_vector = np.fromfile(cvecfile, dtype=np.float64)

    return ci_vector.reshape((num_rows, num_cols))


# NOTE: Commented out because it appears unfunctional. Looks for variable "orbs"
# but it is never declared. Preserving function for now...
# def write_ci_vector(ci_vector, orbfile):
#     """Serialize a TeraChem binary CI vector file of doubles.

#     Args:
#         ci_vector: Non-flat NumPy array of CI vector
#         cvecfile: Filename of CI vector file to write
#     """
#     if not isinstance(orbs, np.ndarray) or len(orbs.shape) != 2:
#         raise SyntaxError(
#             "Need a shaped NumPy array for write_cvecfile to do proper serialization for TeraChem."
#         )

#     ci_vector.astype(np.float64).tofile(orbfile)
