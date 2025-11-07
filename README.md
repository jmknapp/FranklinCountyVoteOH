# Franklin Shifts

**Production-quality geospatial analysis of precinct-level partisan shifts in Franklin County, Ohio (2006→present)**

Franklin Shifts is a Python pipeline for harmonizing election results across changing precinct boundaries. It builds spatial crosswalks between different precinct vintages, reallocates historical votes onto a common base geography, and produces comprehensive time-series analysis with maps and visualizations.

---

## Features

- ✅ **Spatial Harmonization**: Automatically build crosswalks between any pair of precinct geographies
- ✅ **Flexible Weighting**: Area-based or population-based vote reallocation
- ✅ **Time-Series Analysis**: Compute two-party shares, swings, turnout changes across elections
- ✅ **Visualization**: Generate static PNG choropleths and interactive Leaflet/Folium HTML maps
- ✅ **Production-Ready**: Comprehensive logging, error handling, and test coverage
- ✅ **CLI Interface**: Simple command-line tools with Typer
- ✅ **Reproducible**: YAML configuration, example data, and CI-ready tests

---

## Quick Start

### Installation

```bash
# Clone or download this repository
cd franklin-shifts

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or use the Makefile
make setup
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `config/project.yaml` to specify:
   - Base year for harmonization
   - Coordinate reference system
   - Paths to your shapefiles and CSV files
   - Precinct ID field names

### Basic Usage

```bash
# 1. Validate configuration
python -m src.cli init

# 2. Harmonize all years to base geography
python -m src.cli harmonize-all

# 3. Compute metrics (D_share, swings, turnout)
python -m src.cli metrics

# 4. Create maps
python -m src.cli maps 2024 D_share
python -m src.cli maps 2024 swing_vs_2008

# 5. View summary statistics
python -m src.cli summary
```

### Demo with Synthetic Data

Run the complete pipeline on synthetic example data:

```bash
python -m src.cli demo
# Or using the Makefile
make demo
```

This creates synthetic precincts with different boundaries across years, harmonizes them, computes metrics, and generates maps.

---

## Project Structure

```
franklin-shifts/
├── README.md                    # This file
├── pyproject.toml              # Project metadata and dependencies
├── requirements.txt            # Python dependencies
├── Makefile                    # Convenience targets
├── .env.example                # Environment variables template
├── config/
│   └── project.yaml            # Project configuration
├── data/
│   ├── raw/                    # Input shapefiles and CSVs (user-provided)
│   ├── interim/                # Crosswalks and intermediate files
│   ├── processed/              # Output GeoPackages, CSVs, maps
│   └── examples/               # Synthetic demo data
├── src/
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface (Typer)
│   ├── io_utils.py             # Load shapefiles, CSVs, validate data
│   ├── crosswalk.py            # Build spatial crosswalks
│   ├── harmonize.py            # Reallocate votes to base geography
│   ├── metrics.py              # Compute partisan metrics and aggregates
│   ├── visualize.py            # Create maps (static PNG, interactive HTML)
│   └── demo.py                 # Generate synthetic example data
└── tests/
    ├── test_crosswalk.py
    ├── test_harmonize.py
    └── test_metrics.py
```

---

## CLI Commands

The `ffs` command-line tool provides the following commands:

### `ffs init`
Validate configuration, check dependencies, create output directories.

```bash
ffs init
ffs init --config custom_config.yaml
```

### `ffs crosswalk`
Build spatial crosswalk from a past year to base geography.

```bash
ffs crosswalk 2008                    # Area-weighted (default)
ffs crosswalk 2008 --weight pop       # Population-weighted
```

### `ffs harmonize`
Reallocate votes from a single year to base geography.

```bash
ffs harmonize 2016
ffs harmonize 2016 --weight area
```

### `ffs harmonize-all`
Process all non-base years in batch.

```bash
ffs harmonize-all
ffs harmonize-all --weight pop
```

### `ffs metrics`
Compute time-series metrics: D_share, swings, turnout changes.

```bash
ffs metrics
```

Outputs:
- `data/processed/timeseries_per_precinct.csv` (long format)
- `data/processed/timeseries_per_precinct_wide.csv` (wide format)
- `data/processed/county_aggregates.csv` (county-level totals)

### `ffs maps`
Create static and interactive maps for a year and metric.

```bash
ffs maps 2024 D_share
ffs maps 2020 swing_vs_2008
ffs maps 2024 turnout
```

Outputs:
- `data/processed/maps/{year}_{metric}.png` (static choropleth)
- `data/processed/interactive/{year}_{metric}.html` (interactive Folium map)

### `ffs summary`
Display county-wide aggregates and trends.

```bash
ffs summary
```

### `ffs demo`
Run complete pipeline on synthetic example data.

```bash
ffs demo
```

---

## Configuration

The `config/project.yaml` file controls all aspects of the pipeline:

```yaml
# Base year for harmonization (all others map to this)
base_year: 2024

# Coordinate reference system (NAD83 / Ohio South)
crs: "EPSG:3734"

# Precinct ID field names by year
id_fields:
  2024: "PREC_ID"
  2022: "PREC_ID"
  2020: "PREC_ID"
  # ... add more years

# Paths to shapefiles and results CSVs
paths:
  shapefiles:
    "2024": "data/raw/precincts_2024/precincts_2024.shp"
    "2022": "data/raw/precincts_2022/precincts_2022.shp"
    # ... add more years
  
  results_csv:
    "2024": "data/raw/results_2024.csv"
    "2022": "data/raw/results_2022.csv"
    # ... add more years

# Optional: Census blocks for population weighting
weights:
  blocks_gpkg: null  # Path to census blocks GeoPackage
  block_pop_field: null  # Population field name
  block_year_map: {}  # Map years to block vintages

# Output paths
output:
  harmonized_gpkg: "data/processed/harmonized.gpkg"
  timeseries_csv: "data/processed/timeseries_per_precinct.csv"
  county_aggregates_csv: "data/processed/county_aggregates.csv"
  maps_dir: "data/processed/maps"
  interactive_dir: "data/processed/interactive"
  crosswalk_dir: "data/interim/crosswalks"

# Processing options
options:
  overlap_warning_threshold: 0.98  # Warn if coverage < 98%
  sliver_tolerance: 1e-9  # Minimum area for intersections
  default_weight_method: "area"  # "area" or "pop"
```

---

## Input Data Format

### Shapefiles ✅ INCLUDED

**Franklin County precinct shapefiles for 2006-2024 are already downloaded and included in this repository!**

Downloaded from: [Franklin County Board of Elections](https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files)

Location: `data/raw/precincts_YYYY/`

Each year has:
- **Geometry**: Polygon precinct boundaries
- **ID Field**: Precinct identifier (inspect with `python scripts/inspect_shapefiles.py`)
- **CRS**: Will be reprojected to EPSG:3734 automatically

See `data/raw/README.md` and `DATA_SOURCES.md` for details.

### Results CSVs ⚠️ YOU NEED TO ADD THESE

You must download election results and create CSV files for each year:

Download from: [Franklin County Board of Elections - Election Info](https://vote.franklincountyohio.gov/election-info/)

Required format:
```csv
PRECINCT,D_votes,R_votes
A001,450,350
A002,520,480
```

Save as: `data/raw/results_YYYY.csv`

---

## How It Works

### 1. Spatial Crosswalk

For each historical year, the pipeline:
1. Loads past and base precinct geometries
2. Computes spatial intersection (overlay)
3. Calculates overlap weights:
   - **Area weights**: `frac = area(intersection) / area(past_precinct)`
   - **Population weights** (optional): Uses census blocks to compute population-based ratios

### 2. Vote Reallocation

For each base precinct:
```
harmonized_votes = Σ (past_votes × overlap_fraction)
```

This preserves total vote counts while mapping to new boundaries.

### 3. Metrics Computation

- **D_share**: Democratic two-party vote share (`D_votes / (D_votes + R_votes)`)
- **Swing (YoY)**: Change in D_share from previous election
- **Swing vs Base**: Change in D_share compared to a reference year
- **Turnout**: Total votes cast
- **Turnout Change**: Absolute and percentage change in turnout

### 4. Visualization

- **Static Maps**: Matplotlib choropleths with diverging/sequential colormaps
- **Interactive Maps**: Folium/Leaflet HTML with tooltips, zoom, and basemaps

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Or use the Makefile
make test
```

### Code Formatting

```bash
# Format code
black src/ tests/
ruff check src/ tests/ --fix

# Or use the Makefile
make lint
```

### Project Dependencies

Core libraries:
- **GeoPandas**: Spatial data handling
- **Shapely 2.0**: Geometry operations (vectorized)
- **Pyproj**: Coordinate system transformations
- **rtree**: Spatial indexing
- **Pandas**: Tabular data
- **Matplotlib**: Static visualization
- **Folium**: Interactive maps
- **Typer**: CLI framework
- **PyYAML**: Configuration

Development:
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting

---

## Performance Notes

- **Spatial Index**: Uses rtree for efficient overlay operations
- **Vectorized Operations**: Shapely 2.0 vectorized functions for speed
- **Memory Management**: Processes years sequentially to avoid memory issues
- **Large Datasets**: For counties with >1000 precincts, expect 5-15 minutes per year

---

## Troubleshooting

### CRS Mismatch Errors
Ensure all shapefiles use a consistent CRS or specify `crs` in config for automatic reprojection.

### Missing Precincts
If a precinct exists in the shapefile but not in results CSV (or vice versa), the pipeline will log warnings and treat missing data as zeros.

### Low Coverage Warnings
If spatial overlay covers <98% of source area, check for:
- Geometry errors (use `gdf.is_valid` and `gdf.buffer(0)`)
- CRS mismatches
- Boundary digitization differences

### Memory Issues
For very large datasets:
- Process years individually with `ffs harmonize <year>`
- Reduce precision in shapefiles
- Use population weighting with aggregated blocks

---

## Citation

If you use this tool in research or publications, please cite:

```
Franklin Shifts - Precinct-level partisan shift analysis
https://github.com/yourorg/franklin-shifts
```

---

## License

MIT License - see LICENSE file for details.

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

## Contact

For questions, issues, or feature requests, please open an issue on GitHub.

---

## Acknowledgments

- Ohio Secretary of State for precinct shapefiles
- U.S. Census Bureau for TIGER/Line boundaries
- OpenStreetMap contributors for basemaps

