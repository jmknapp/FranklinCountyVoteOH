# Changelog

All notable changes to Franklin Shifts will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-06

### Added
- Initial release of Franklin Shifts
- Spatial crosswalk building with area and population weighting
- Vote harmonization across precinct boundaries
- Time-series metrics computation (D_share, swings, turnout)
- Static PNG and interactive HTML map generation
- CLI interface with Typer
- Comprehensive test suite
- Demo pipeline with synthetic data
- Full documentation and examples

### Features
- `ffs init` - Initialize and validate configuration
- `ffs crosswalk` - Build spatial crosswalks
- `ffs harmonize` - Reallocate votes to base geography
- `ffs harmonize-all` - Process all years in batch
- `ffs metrics` - Compute partisan metrics
- `ffs maps` - Create visualizations
- `ffs summary` - Display county aggregates
- `ffs demo` - Run example pipeline

### Technical
- Python 3.11+ support
- GeoPandas, Shapely 2.0, Pandas stack
- Production-ready logging and error handling
- CI/CD with GitHub Actions
- MIT License

