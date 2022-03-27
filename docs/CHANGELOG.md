# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.1]

### Changed

- Moved `job_output_to_atomic_result` to be method on client objects so that `AtomicResult.provenance` can be dynamically set correctly depending on which client is used.

## [0.10.0]

### Added

- Documentation and `mkdocs` website on GitHub pages. Docs available [here](https://mtzgroup.github.io/tcpb-client/)

### Changed

- Renamed `AtomicInput.extras['tcfe:config']` -> `AtomicInput.extras['tcfe:keywords']`

## [0.9.0]

### Added

- Configuration parameters for controlling `TCFrontEndClient` behavior:

  1. `native_files`: list[str] - List of natives files to collect. If none passed, all files will be collected.

- Tests for `TCFrontEndClient` file put/get behaviors.

### Changed

- Refactored `TCFrontEndClient`

### Removed

- Construction of molden file from protocol buffer outputs. Molden files can now be requested directly from the Frontend client.

## [0.8.1]

### Added

- `TCFrontEndClient` to enable access to the files written by TeraChem and upload input files for TeraChem, in particular `c0` files as initial wavefunction guesses.

  - Configuration parameters for controlling `TCFrontEndClient` behavior are
    found in `AtomicInput.extras['tcfe:config']` and include:
    1. `c0` | `ca0` and `cb0`: `bytes` - Binary files to use as an initial guess
       wavefunction
    2. `scratch_messy`: `bool` - If `True` client will not delete files on server
       after a computation
    3. `uploads_messy`: `bool` - If `True` client will not delete uploaded c0
       file(s) after a computation
  - Client also supports [AtomicResultProtocols](https://github.com/MolSSI/QCElemental/blob/cabec4a7d1095b656320f2c842f0e132149e4bd1/qcelemental/models/results.py#L538) `stdout` and `native_files`.

### Changed

- `qcelemental` required version bumped from `>=0.17.0` to `>=0.24.0` to support `native_files` field for returning files. See [qcelemental note](https://github.com/MolSSI/QCElemental/blob/cabec4a7d1095b656320f2c842f0e132149e4bd1/docs/source/changelog.rst#0240--2021-11-18). Note I am breaking the convention and returning binary data as well since I have more control over file access via the `TCFrontEndClient` than anticipated in the `qcelemental`/`qcengine` specification. Additionally I need the binary `c0` file to use as initial guesses for TeraChem computations.

### Removed

## [0.8.0] - 2021-05-26

### Added

- Many IMD values to the `result.extra['qcvars']` dict
- `result.wavefunction` now contains `WavefunctionProperties`

### Changed

- `result.extras['qcvars']['bond_order']` -> `result.extras['qcvars']['meyer_bond_order']`
- Many values in `result.extras['qcvars']` moved to `result.extras['job_extras']` if they didn't pertain to quantum chemistry values.
- `result.extras['qcvars']['orb{a,b}_{energies,occupations}']` moved to `result.wavefunction`. Note these will only be returned if `AtomicInput.protocols.wavefunction = "all"`.

### Removed

- Removed unused documentation setup. Can add documentation with `mkdocs` later if needed.

## [0.7.2] - 2021-03-10

### Changed

- Learned that AtomicResult is supposed to be a full superset of AtomicInput used to generate the result. Changed `utils.job_output_to_atomic_result()` to reflect this reality.

## [0.7.1] - 2021-03-10

### Added

- `imd_orbital_type` specific keyword extraction to support creation of molden files.

## [0.7.0] - 2021-02-26

### Added

- `TCCloud.compute(atomic_input: AtomicInput) -> AtomicResult` top level method to create MolSSI QCSchema compliant interface.
- `pyproject.toml`
- more examples in `/examples` that leverage the new QCSchema interface
- `utils.py` that contains basic utilities for transforming inputs/outputs to `QCSchema` format.

### Changed

- Using `flit` instead of `setuptools` for packaging.
- Compatible with only python 3.6+ (adding type annotations)

### Removed

- `setup.py`
- Unused and broken test files including non functional mock server.

## [r0.6.0] - 2021-02-25

### Changed

- Added Henry's molden file constructor function.

## 0.5.x - Long long ago

### Added

- All of Stefan's original code.

[unreleased]: https://github.com/mtzgroup/tcpb-client/compare/0.10.1...HEAD
[0.10.1]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.10.1
[0.10.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.10.0
[0.9.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.9.0
[0.8.1]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.8.1
[0.8.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.8.0
[0.7.2]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.7.2
[0.7.1]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.7.1
[0.7.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/0.7.0
[r0.6.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.6.0
[r0.5.3]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.5.3
[r0.5.2]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.5.2
[r0.5.1]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.5.1
[r0.5.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.5.0
[r0.4.1]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.4.1
[r0.4.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.4.0
[r0.3.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.3.0
[r0.2.0]: https://github.com/mtzgroup/tcpb-client/releases/tag/r0.2.0
