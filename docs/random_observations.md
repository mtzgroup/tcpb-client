# Random Observations

This document provides some rough usage documentation notes.

## guess vs orb1afile/orb1bfile

If you want to use a guess wavefunction for a subsequent calculation (i.e., pass the `c0` file from TeraChem to a new calculation):

- For an energy/gradient calculation you pass the `path/to/c0` using the keyword `guess` in the `user_options` field. See `examples/guess_reuse_example.py` and note the passing of a string that indicates the filepath on the server than TeraChem should use:

  - Closed shell `guess=path/to/c0`
  - Open shell `guess=path/to/ca0 path/to/cb0`
    - Note with open shell the filenames change from `c0` -> `ca0` and `cb0`

- For ci_overlap computations you pass the `c0` file in the `orb1afile` and `orb1bfile` fields. See `examples/ci_overlap_example.py`

I (Colton) do not understand why this difference exists. It seems to be an artifact of not noticing there are multiple ways to pass the same file and perhaps should be remedied in a future release of the TeraChem PB server.
