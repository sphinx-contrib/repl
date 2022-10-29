# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1] - 2022-10-29

### Added

- call `makedirs` in `mpl_init()` to make sure build directory exists

## [0.4.0] - 2022-10-27

### Added

- tabular display of Matplotlib figures
- `table_*` directive options added

## [0.2.0] - 2022-10-25

### Added

- `image_*` directive options added

### Changed

- Renamed Matplotlib directive options by adding the prefix `mpl_`

## [0.2.0] - 2022-10-24

### Added

- Matplotlib integration
- Added visibility control options and magic comments (see Readme)

### Changed

- Moved module from `sphinxcontrib_repl` to `sphinxcontrib.repl`
- Call current executable instead of fixed `python` command

## [0.1.0] - 2022-10-18

### Added

- First release

[unreleased]: https://github.com/sphinx-contrib/repl/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/sphinx-contrib/repl/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/sphinx-contrib/repl/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/sphinx-contrib/repl/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sphinx-contrib/repl/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sphinx-contrib/repl/compare/aa188e...v0.1.0
