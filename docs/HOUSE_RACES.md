# Extracting House Race Results

This guide explains how to extract Congressional District (House) race results from Franklin County's "group detail" election results files.

## Background

Franklin County election results come in two formats:

1. **Standard Results** - One row per precinct, all races in columns
2. **Group Detail Results** - Multiple rows per precinct, split by State Legislative districts

The **group detail** format is essential for extracting House races because:
- Precincts can span multiple Congressional Districts
- The detail file splits each precinct by State Legislative district
- Each row shows votes for only the House candidates in that district
- This allows proper separation of CD-03 vs CD-15 results

## Quick Start

### Extract All House Races

```bash
python scripts/preprocess_results.py \
    data/raw/boe_downloads/2024general_detail.xlsx \
    --detail-file \
    --extract-house \
    --year 2024
```

**Output:**
- `data/raw/results_2024_house_cd03.csv` - CD-03 results (Joyce Beatty's district)
- `data/raw/results_2024_house_cd15.csv` - CD-15 results (Mike Carey's district)

### Extract Specific Congressional District

```bash
python scripts/preprocess_results.py \
    data/raw/boe_downloads/2024general_detail.xlsx \
    --detail-file \
    --extract-house \
    --cd CD-03 \
    --year 2024
```

## 2024 Franklin County Results

### CD-03 (Columbus core, eastern suburbs)
- **Democratic**: Joyce Beatty
- **Republican**: Michael Young
- **Result**: Beatty 70.7% - Young 29.3%
- **Precincts**: 540

### CD-15 (Columbus south, western/southern suburbs)
- **Democratic**: Adam Miller
- **Republican**: Mike Carey
- **Result**: Carey 56.3% - Miller 43.7%
- **Precincts**: 353

**Note**: Some precincts are split between districts (total = 893 vs 889 county precincts).

## Running Time-Series Analysis

Once you've extracted House race results, run separate harmonization pipelines for each CD:

```bash
# CD-03 time series
python -m src.cli harmonize \
    --results-csv data/raw/results_2024_house_cd03.csv \
    --race-name "House CD-03" \
    --output data/processed/cd03_harmonized.csv

python -m src.cli visualize \
    --harmonized-csv data/processed/cd03_harmonized.csv \
    --output-dir data/processed/maps/cd03/

# CD-15 time series
python -m src.cli harmonize \
    --results-csv data/raw/results_2024_house_cd15.csv \
    --race-name "House CD-15" \
    --output data/processed/cd15_harmonized.csv

python -m src.cli visualize \
    --harmonized-csv data/processed/cd15_harmonized.csv \
    --output-dir data/processed/maps/cd15/
```

## Cross-Race Comparisons

You can compare Presidential, Senate, and House results for the same year:

```bash
# Extract all races for 2024
python scripts/preprocess_results.py \
    data/raw/boe_downloads/2024general.xlsx \
    --sheet "25ElectionResultsCSV" \
    --dem-candidate "Harris" \
    --rep-candidate "Trump" \
    --year 2024 \
    --output data/raw/results_2024_president.csv

# (Presidential results already extracted as results_2024.csv)
# (Senate results already extracted as results_2024_senate.csv)
# (House results already extracted as results_2024_house_cd*.csv)

# Create comparison maps
python -c "
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Load all 2024 races
pres = pd.read_csv('data/raw/results_2024.csv')
senate = pd.read_csv('data/raw/results_2024_senate.csv')
cd03 = pd.read_csv('data/raw/results_2024_house_cd03.csv')

# Calculate D shares
pres['D_share'] = pres['D_votes'] / (pres['D_votes'] + pres['R_votes'])
senate['D_share'] = senate['D_votes'] / (senate['D_votes'] + senate['R_votes'])
cd03['D_share'] = cd03['D_votes'] / (cd03['D_votes'] + cd03['R_votes'])

# Merge
merged = pres[['PRECINCT']].copy()
merged = merged.merge(pres[['PRECINCT', 'D_share']], on='PRECINCT', suffixes=('', '_pres'))
merged = merged.merge(senate[['PRECINCT', 'D_share']], on='PRECINCT', suffixes=('', '_sen'))
merged = merged.merge(cd03[['PRECINCT', 'D_share']], on='PRECINCT', how='left', suffixes=('', '_cd03'))

# Calculate ticket splitting
merged['pres_vs_senate'] = merged['D_share_sen'] - merged['D_share_pres']
merged['pres_vs_house'] = merged['D_share_cd03'] - merged['D_share_pres']

print('Countywide Democratic Performance:')
print(f'  Presidential (Harris): {100*pres[\"D_share\"].mean():.1f}%')
print(f'  Senate (Brown):        {100*senate[\"D_share\"].mean():.1f}%')
print(f'  House CD-03 (Beatty):  {100*cd03[\"D_share\"].mean():.1f}%')
"
```

## Historical Data

To build time-series for House races, you'll need:

1. Historical "group detail" files (if available)
2. OR manually create CD-specific CSVs from standard results
3. Account for redistricting (Congressional district boundaries changed in 2022)

**Important**: Congressional district boundaries were redrawn after the 2020 Census. For accurate time-series:
- 2012-2020: Use old CD boundaries
- 2022-present: Use new CD boundaries
- 2021: Special election year, check which boundaries were used

You may need separate crosswalks for pre/post-redistricting periods.

## Updating for Future Elections

The script currently hardcodes 2024 House candidates:

```python
house_races = {
    'CD-03': {
        'D': 'Dem Joyce Beatty',
        'R': 'Rep Michael Young'
    },
    'CD-15': {
        'D': 'Dem Adam Miller',
        'R': 'Rep Mike Carey'
    }
}
```

For future elections, edit `scripts/preprocess_results.py` and update the candidate names in the `extract_house_races_from_detail()` function.

## Troubleshooting

### Precinct Names Don't Match Shapefile

The script automatically fixes common formatting differences:
- Zero-pads single-digit precinct numbers (`BEXLEY 1-A` → `BEXLEY 01-A`)
- Handles multi-word precinct names (`UPPER ARLINGTON 5-D` → `UPPER ARLINGTON 05-D`)
- Converts to uppercase

Current match rates:
- **CD-03**: 100% (540/540 precincts)
- **CD-15**: 98.6% (348/353 precincts)

### Wrong Congressional District Assignments

The script assigns each row to a CD based on which House race has votes. If a row has votes for both CDs (unusual), it assigns to the CD with more votes.

### Missing Historical Data

If detail files aren't available for historical elections, you can:
1. Request them from the Franklin County Board of Elections
2. Use GIS overlay analysis to determine CD assignments
3. Accept precinct-level approximations (some error in split precincts)

## See Also

- [Preprocessing Results Guide](PREPROCESSING_RESULTS.md) - For Presidential/Senate/Statewide races
- [QUICKREF.md](../QUICKREF.md) - Quick reference for all commands
- [WORKFLOW_SUMMARY.md](WORKFLOW_SUMMARY.md) - Complete analysis workflow

