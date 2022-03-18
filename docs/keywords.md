# Keywords

Important keywords for controlling the behavior of the clients.

## TCFrontEndClient

All keywords for controlling the [TCFrontEndClient][tcpb.clients.TCFrontEndClient] should be placed in `AtomicInput.extras["tcfe:keywords"]` under the keys noted below:

| Keywords              | Type        | Description                                                                                                                                                                                                                                                                                                                      | Default Value |
| --------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `scratch_messy`       | `bool`      | If set to `True` the scratch directory will not be cleaned up (deleted) after a compute job                                                                                                                                                                                                                                      | `False`       |
| `uploads_messy`       | `bool`      | If set to `True` the uploaded files will not be cleaned up (deleted) after a compute job                                                                                                                                                                                                                                         | `False`       |
| `native_files`        | `list[str]` | If used in conjunction with `AtomicInput.protocols = {"native_files": "all"}` only the filenames listed in the array will be returned. This is useful when only a single file is needed and the overhead of downloading potentially many files is large.                                                                         | `None`        |
| `c0` or `ca0 and cb0` | `binary`    | TeraChem's c0 file(s) to be put on the server as an initial guess wavefunction. If included, they will be automatically uploaded and the `AtomicInput` will be modified to pass the `guess` keyword to TeraChem referencing the wave function files. See [FrontEnd Guess Reuse](../Examples/frontend_guess_reuse) for an example | `None`        |

::: tcpb.config:TCFEKeywords
