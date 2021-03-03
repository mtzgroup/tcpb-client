# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Added `imd_orbital_type` to specific keyword extraction to support creation of molden files.

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

[Unreleased]: https://github.com/mtzgroup/tcpb-client/compare/0.7.0...HEAD
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