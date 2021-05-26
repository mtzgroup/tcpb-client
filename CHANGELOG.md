# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

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

[unreleased]: https://github.com/mtzgroup/tcpb-client/compare/0.8.0...HEAD
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
