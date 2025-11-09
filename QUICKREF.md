# Quick Reference Card

## One-Page Cheat Sheet for Franklin Shifts

### Installation
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Data Acquisition

**Shapefiles** (Already Downloaded ✅)
```bash
./scripts/download_shapefiles.sh
```
Result: `data/raw/precincts_YYYY/`

**Election Results** (You Need To Do ⚠️)
1. Download from https://vote.franklincountyohio.gov/election-info/
2. Save to `data/raw/boe_downloads/YYYY_general.xlsx`
3. Extract one race per year using preprocessing script:

```bash
# List available sheets
python scripts/preprocess_results.py data/raw/boe_downloads/2020_general.xlsx --list-sheets

# Extract Presidential/Senate/Statewide race
python scripts/preprocess_results.py data/raw/boe_downloads/2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020

# Extract House races (requires "group detail" file)
python scripts/preprocess_results.py data/raw/boe_downloads/2024_general_detail.xlsx \
    --detail-file \
    --extract-house \
    --year 2024

# Extract 2025 turnout (ballots vs registered)
python scripts/extract_turnout_2025.py
```

See `docs/HOUSE_RACES.md` for Congressional District analysis.

### Configuration

Edit `config/project.yaml`:
- Set `base_year` (default: 2025)
- Update `id_fields` if shapefile columns differ
- Verify `results_csv` paths

### CLI Commands

```bash
# Validate setup
ffs init

# Build crosswalk for one year
ffs crosswalk 2008

# Harmonize one year
ffs harmonize 2008

# Harmonize all years
ffs harmonize-all

# Compute metrics
ffs metrics

# Create maps
ffs maps 2024 D_share
ffs maps 2024 swing_vs_2008

# View summary
ffs summary

# Run demo with synthetic data
ffs demo
```

### Complete Pipeline

```bash
./scripts/run_pipeline.sh
```

Or step by step:
```bash
python -m src.cli init
python -m src.cli harmonize-all
python -m src.cli metrics
python -m src.cli maps 2025 D_share
python -m src.cli summary
```

### Output Files

```
data/processed/
├── harmonized.gpkg              # GeoPackage (QGIS/ArcGIS)
├── timeseries_per_precinct.csv  # Long format
├── timeseries_per_precinct_wide.csv  # Wide format
├── county_aggregates.csv        # County totals
├── maps/                        # Static PNG maps
└── interactive/                 # Interactive HTML maps
```

### Common Issues

| Issue | Fix |
|-------|-----|
| Column not found | Update `id_fields` in config |
| File not found | Run preprocessing or comment out year |
| CRS mismatch | Auto-handled by pipeline |
| Low coverage warning | Expected - boundaries changed |

### Recommended Race Choices

| Year | Best Race |
|------|-----------|
| Even years (Presidential) | Presidential |
| Even years (Midterm) | Governor |
| Odd years | Skip or use best available |

**Goal:** Top-of-ticket races for consistent partisan measure

### Key Metrics

- **D_share**: Democratic two-party vote share (0-1)
- **swing_yoy**: Change from previous election
- **swing_vs_YYYY**: Change vs. baseline year
- **turnout**: Total votes cast
- **turnout_change_yoy_pct**: Turnout change %

### Documentation

- `README.md` - Main documentation
- `docs/QUICKSTART.md` - Detailed setup
- `docs/PREPROCESSING_RESULTS.md` - Results extraction help
- `docs/HOUSE_RACES.md` - Congressional District analysis
- `docs/WORKFLOW_SUMMARY.md` - Complete workflow
- `SHAPEFILES_DOWNLOADED.md` - Shapefile status

### Help

```bash
# CLI help
ffs --help
ffs <command> --help

# Run tests
pytest tests/ -v

# Format code
make lint

# Demo
make demo
```

### Example Analysis (Python)

```python
import pandas as pd

# Load data
df = pd.read_csv('data/processed/timeseries_per_precinct.csv')

# Filter to precinct
p = df[df['PREC_ID'] == 'YOUR_PRECINCT']

# Plot trend
p.plot(x='year', y='D_share', marker='o')
```

### Expected Processing Time

- Preprocessing: 1-2 hours (one-time)
- Harmonization: 1-3 hours (13 years)
- Metrics: 5 minutes
- Maps: 10 minutes

### Contact

Franklin County BOE: 614-525-3100  
Website: https://vote.franklincountyohio.gov/

