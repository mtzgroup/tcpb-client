from numpy import array

correct_answer = {
    "atoms": array([b"O", b"H", b"H"], dtype="|S2"),
    "geom": array( # not validated
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    ),
    "mm_geom": array( # not validated
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    ),
    "charges": array(
        [-0.766267, 0.407570, 0.358697]
    ),
    "spins": array([10.0, 10.0, 10.0]), # not validated
    "dipole_moment": 2.436694,
    "dipole_vector": array([1.544914, 1.884333, -0.002387]),
    "energy": [-75.5924554235],
    "gradient": array(
        [
            0.0105322205, 0.0078665231, -0.0009857979,
            -0.0134444489, -0.0017209821, 0.0014285024,
            -0.0015016529, -0.0054770400, 0.0002736808,
        ]
    ),
    "mm_gradient": array(
        [
            0.0060331657, -0.0020276564, -0.0003713350,
            0.0120386663, 0.0078254434, -0.0494778492,
            -0.0136579540, -0.0064662907, 0.0491327989,
        ]
    ),
    "orb_energies": array( # not validated
        [
            -11.23750969,
            4.90688612,
        ]
    ),
    "orb_occupations": array( # not validated
        [
            2.0,
            0.0,
        ]
    ),
    "bond_order": array( # not validated
        [
            [
                0,
            ],
        ]
    ),
}
