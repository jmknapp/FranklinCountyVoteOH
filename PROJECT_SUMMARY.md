# Franklin Shifts - Project Summary

## Overview

**Franklin Shifts** is a production-quality Python geospatial analysis pipeline for studying precinct-level partisan shifts in Franklin County, Ohio from 2006 to present. It harmonizes election results across changing precinct boundaries using sophisticated spatial crosswalks.

## Completed Features

### ✅ Core Functionality

1. **Spatial Crosswalk Building** (`src/crosswalk.py`)
   - Area-weighted allocation (default)
   - Population-weighted allocation (with census blocks)
   - Vectorized operations with Shapely 2.0
   - Spatial indexing with rtree for performance
   - Comprehensive validation and coverage checks

2. **Vote Harmonization** (`src/harmonize.py`)
   - Reallocate historical votes to base geography
   - Batch processing for all years
   - Automatic vote conservation checks
   - GeoPackage and CSV outputs

3. **Metrics Computation** (`src/metrics.py`)
   - Democratic two-party share
   - Year-over-year swings
   - Swings vs. baseline years
   - Turnout and turnout changes
   - Long and wide format outputs
   - County-level aggregates

4. **Visualization** (`src/visualize.py`)
   - Static PNG choropleths with matplotlib
   - Interactive HTML maps with Folium
   - Customizable colormaps and legends
   - Basemap integration with contextily
   - Comparison maps for multiple years

5. **I/O Utilities** (`src/io_utils.py`)
   - Robust shapefile loading with CRS handling
   - CSV parsing with validation
   - ID normalization and consistency checks
   - Automatic output directory creation

### ✅ Command-Line Interface

Full-featured CLI with Typer and Rich formatting:

- `ffs init` - Configuration validation
- `ffs crosswalk <year>` - Build crosswalk for single year
- `ffs harmonize <year>` - Harmonize single year
- `ffs harmonize-all` - Batch process all years
- `ffs metrics` - Compute time-series metrics
- `ffs maps <year> <metric>` - Create visualizations
- `ffs summary` - Display county aggregates
- `ffs demo` - Run synthetic example pipeline

### ✅ Testing & Quality

1. **Comprehensive Test Suite** (`tests/`)
   - `test_crosswalk.py`: 8 tests for spatial operations
   - `test_harmonize.py`: 6 tests for vote reallocation
   - `test_metrics.py`: 7 tests for metric computation
   - Total: 21+ unit tests
   - Fixtures for synthetic test data
   - Vote conservation validation

2. **Code Quality**
   - Black formatting (100 char line length)
   - Ruff linting (E, W, F, I, B, C4, UP rules)
   - Type hints throughout
   - Comprehensive docstrings
   - Production-grade error handling

3. **CI/CD** (`.github/workflows/ci.yml`)
   - Automated testing on Python 3.11 and 3.12
   - Linting and formatting checks
   - Demo pipeline execution
   - Codecov integration

### ✅ Documentation

1. **Main Documentation**
   - `README.md` - Comprehensive project documentation
   - `docs/QUICKSTART.md` - Step-by-step usage guide
   - `CONTRIBUTING.md` - Contributor guidelines
   - `CHANGELOG.md` - Version history

2. **Configuration**
   - `config/project.yaml` - Well-documented example config
   - `.env.example` - Environment variables template

3. **Code Documentation**
   - Inline docstrings for all functions
   - Type annotations
   - Example usage in docstrings

### ✅ Synthetic Demo Data

- `src/demo.py` - Synthetic data generator
- Creates realistic test scenario:
  - 2024: 4 precincts (2×2 grid)
  - 2022: 3 precincts (different boundaries)
  - 2020: 2 precincts (horizontal split)
- Full pipeline executable with `ffs demo`

### ✅ Project Infrastructure

1. **Build System**
   - `pyproject.toml` - Modern Python packaging
   - `requirements.txt` - Dependency list
   - `setup.cfg` - Tool configurations
   - `Makefile` - Convenience targets

2. **Version Control**
   - `.gitignore` - Comprehensive exclusions
   - `.gitkeep` files for data directories
   - LICENSE - MIT License

3. **Scripts**
   - `scripts/run_pipeline.sh` - Complete pipeline runner

## File Structure

```
franklin-shifts/
├── README.md                      # Main documentation
├── PROJECT_SUMMARY.md             # This file
├── CHANGELOG.md                   # Version history
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # MIT License
├── pyproject.toml                 # Project metadata
├── requirements.txt               # Dependencies
├── Makefile                       # Build targets
├── .env.example                   # Environment template
├── .gitignore                     # Git exclusions
│
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI
│
├── config/
│   └── project.yaml               # Project configuration
│
├── docs/
│   └── QUICKSTART.md              # Quick start guide
│
├── scripts/
│   └── run_pipeline.sh            # Pipeline runner script
│
├── data/
│   ├── raw/                       # Input data (user-provided)
│   ├── interim/                   # Crosswalks
│   ├── processed/                 # Outputs
│   │   ├── maps/                  # Static PNG maps
│   │   └── interactive/           # Interactive HTML maps
│   └── examples/                  # Synthetic demo data
│
├── src/
│   ├── __init__.py                # Package init
│   ├── cli.py                     # CLI interface (320 lines)
│   ├── io_utils.py                # I/O utilities (180 lines)
│   ├── crosswalk.py               # Spatial crosswalks (300 lines)
│   ├── harmonize.py               # Vote reallocation (240 lines)
│   ├── metrics.py                 # Metrics computation (250 lines)
│   ├── visualize.py               # Visualization (320 lines)
│   └── demo.py                    # Synthetic data (180 lines)
│
└── tests/
    ├── __init__.py                # Test package init
    ├── conftest.py                # Pytest configuration
    ├── test_crosswalk.py          # Crosswalk tests (180 lines)
    ├── test_harmonize.py          # Harmonization tests (160 lines)
    └── test_metrics.py            # Metrics tests (140 lines)
```

## Key Dependencies

- **GeoPandas 0.14+** - Spatial data handling
- **Shapely 2.0+** - Vectorized geometry operations
- **Pandas 2.1+** - Tabular data processing
- **Matplotlib 3.8+** - Static visualization
- **Folium 0.15+** - Interactive maps
- **Typer 0.9+** - CLI framework
- **Rich 13.0+** - Terminal formatting
- **PyYAML 6.0+** - Configuration files
- **pytest 7.4+** - Testing framework

## Technical Highlights

### Performance Optimizations
- Spatial indexing with rtree
- Vectorized Shapely 2.0 operations
- Efficient pandas operations
- Progress bars with tqdm

### Robustness Features
- Comprehensive error handling
- Logging at all levels
- Data validation and consistency checks
- Graceful handling of missing data
- CRS transformation and validation

### Production-Ready Design
- Defensive coding practices
- Type hints throughout
- Comprehensive test coverage
- CI/CD pipeline
- Clear error messages
- Progress indicators

## Usage Example

```bash
# Setup
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit config/project.yaml with your data paths

# Run pipeline
python -m src.cli init
python -m src.cli harmonize-all
python -m src.cli metrics
python -m src.cli maps 2024 D_share
python -m src.cli summary

# Or run everything at once
./scripts/run_pipeline.sh
```

## Output Files

1. **GeoPackage**: `data/processed/harmonized.gpkg`
   - Layers: `yr_2006_on_2024`, `yr_2008_on_2024`, etc.
   - Base geometry with harmonized votes

2. **CSVs**:
   - `timeseries_per_precinct.csv` - Long format
   - `timeseries_per_precinct_wide.csv` - Wide format
   - `county_aggregates.csv` - County totals

3. **Maps**:
   - `maps/{year}_{metric}.png` - Static images
   - `interactive/{year}_{metric}.html` - Interactive web maps

4. **Crosswalks**: `interim/crosswalks/crosswalk_{year}_to_{base}.csv`

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Demo pipeline
python -m src.cli demo
```

## Status

✅ **COMPLETE** - All requirements from initial prompt fulfilled:

1. ✅ Ingests shapefiles + CSVs per year
2. ✅ Builds spatial crosswalks (any year → base)
3. ✅ Reallocates votes with area/population weights
4. ✅ Produces time-series tables
5. ✅ Exports GeoPackage, CSVs, PNG, and HTML
6. ✅ Logging, tests, synthetic data
7. ✅ Python 3.11, all specified tech stack
8. ✅ CLI with Typer, YAML config
9. ✅ Black + Ruff formatting
10. ✅ Production-quality code

**Total Lines of Code**: ~2,000+ lines across all modules

## Next Steps for Users

1. Add your own precinct shapefiles to `data/raw/`
2. Add election results CSVs
3. Configure `config/project.yaml`
4. Run the pipeline
5. Analyze results!

## License

MIT License - See LICENSE file

