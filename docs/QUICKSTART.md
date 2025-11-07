# Quick Start Guide

This guide will walk you through using Franklin Shifts with your own precinct data.

## Prerequisites

- Python 3.11 or higher
- Precinct shapefiles for each election year
- Election results CSVs with D/R vote counts

## Installation

```bash
# Clone repository
cd franklin-shifts

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Prepare Your Data

### 1. Organize Your Shapefiles

```
data/raw/
├── precincts_2006/
│   └── precincts_2006.shp (+ .shx, .dbf, .prj)
├── precincts_2008/
│   └── precincts_2008.shp
├── ...
└── precincts_2024/
    └── precincts_2024.shp
```

Each shapefile should have:
- Polygon geometries for precincts
- A unique ID field (e.g., `PREC_ID`, `PRECINCT_ID`)
- Projected CRS (will be reprojected automatically)

### 2. Prepare Results CSVs

```
data/raw/
├── results_2006.csv
├── results_2008.csv
├── ...
└── results_2024.csv
```

Each CSV should have at minimum:
```csv
PREC_ID,D_votes,R_votes
A001,450,350
A002,520,480
...
```

Column names can vary - you'll specify them in config.

## Configure the Project

### 1. Copy Environment Template

```bash
cp .env.example .env
```

Edit `.env` if needed (usually defaults are fine).

### 2. Edit `config/project.yaml`

```yaml
# Set your base year (most recent/target geography)
base_year: 2024

# Set your coordinate system (Ohio South: EPSG:3734)
crs: "EPSG:3734"

# Specify ID field names by year
id_fields:
  2024: "PREC_ID"
  2022: "PREC_ID"
  2020: "PRECINCT_ID"  # Can vary by year
  # ... etc

# Point to your files
paths:
  shapefiles:
    "2024": "data/raw/precincts_2024/precincts_2024.shp"
    "2022": "data/raw/precincts_2022/precincts_2022.shp"
    # ... etc
  
  results_csv:
    "2024": "data/raw/results_2024.csv"
    "2022": "data/raw/results_2022.csv"
    # ... etc
```

## Run the Pipeline

### 1. Initialize and Validate

```bash
python -m src.cli init
```

This checks:
- Config file validity
- File paths exist
- Dependencies installed
- Creates output directories

### 2. Harmonize All Years

```bash
python -m src.cli harmonize-all
```

This will:
- Build spatial crosswalks for each year → base year
- Reallocate votes to base geography
- Save outputs to `data/processed/harmonized.gpkg`

Expected runtime: 5-15 minutes per year for typical county.

### 3. Compute Metrics

```bash
python -m src.cli metrics
```

Outputs:
- `data/processed/timeseries_per_precinct.csv` - Long format
- `data/processed/timeseries_per_precinct_wide.csv` - Wide format
- `data/processed/county_aggregates.csv` - County totals

### 4. Create Maps

```bash
# Map Democratic two-party share in 2024
python -m src.cli maps 2024 D_share

# Map partisan swing from 2008 to 2024
python -m src.cli maps 2024 swing_vs_2008

# Map turnout
python -m src.cli maps 2024 turnout
```

Outputs:
- `data/processed/maps/{year}_{metric}.png` - Static image
- `data/processed/interactive/{year}_{metric}.html` - Interactive map

### 5. View Summary

```bash
python -m src.cli summary
```

Displays county-wide results by year in your terminal.

## Explore the Data

### GeoPackage Layers

Open `data/processed/harmonized.gpkg` in QGIS or similar:
- Layers: `yr_2006_on_2024`, `yr_2008_on_2024`, etc.
- Each layer has base 2024 geometry with that year's votes

### Time-Series CSV

```python
import pandas as pd

df = pd.read_csv('data/processed/timeseries_per_precinct.csv')

# Filter to one precinct
precinct_a = df[df['PREC_ID'] == 'A001']

# Plot D_share over time
import matplotlib.pyplot as plt
precinct_a.plot(x='year', y='D_share', kind='line')
plt.show()
```

### Interactive Maps

Open any `.html` file in `data/processed/interactive/` in your web browser:
- Pan and zoom
- Click precincts for details
- Full-screen mode

## Advanced Options

### Population Weighting

If you have census block data:

1. Add to `config/project.yaml`:
```yaml
weights:
  blocks_gpkg: "data/raw/census_blocks.gpkg"
  block_pop_field: "POP10"
```

2. Run with population weights:
```bash
python -m src.cli harmonize-all --weight pop
```

### Process Individual Years

Instead of `harmonize-all`, process one year:

```bash
python -m src.cli harmonize 2008
python -m src.cli harmonize 2012
# ... etc
```

### Custom Config Path

```bash
python -m src.cli init --config custom_config.yaml
python -m src.cli harmonize-all --config custom_config.yaml
```

## Troubleshooting

### "CRS mismatch" error
Make sure `crs` in config matches your preferred projection. Files will be reprojected automatically.

### "Column not found" error
Check that ID field names in `id_fields` match your shapefile attributes.

### Low coverage warnings
Some precincts may not overlap perfectly. Check:
- Geometry validity: `gdf.is_valid`
- Consistent CRS across years
- Boundary accuracy

### Out of memory
For large datasets, process years individually rather than all at once.

## Next Steps

- Explore time-series data in your analysis tool of choice
- Create custom visualizations
- Compute additional metrics
- Share insights!

## Questions?

See the main [README.md](../README.md) or open an issue on GitHub.

