# BOE Downloads Directory

## Purpose

This directory is for storing the **original Excel files** downloaded from the Franklin County Board of Elections website.

## What Goes Here

Place the raw, unmodified Excel files from:
**https://vote.franklincountyohio.gov/election-info/**

### Recommended Naming Convention

```
data/raw/boe_downloads/
├── 2006_general.xlsx
├── 2008_general.xlsx
├── 2010_general.xlsx
├── 2012_general.xlsx
├── 2014_general.xlsx
├── 2016_general.xlsx
├── 2018_general.xlsx
├── 2020_general.xlsx
├── 2022_general.xlsx
├── 2024_general.xlsx
└── [other elections as needed]
```

**Format:** `YYYY_<election_type>.xlsx`

Examples:
- `2020_general.xlsx` - November general election
- `2020_primary.xlsx` - March/May primary election (if needed)
- `2023_general.xlsx` - Odd-year local elections

## Processing Workflow

### 1. Download Files
Download from BOE website and save to this directory.

### 2. Extract Race Data
Use the preprocessing script to extract specific races:

```bash
# From project root
python scripts/preprocess_results.py data/raw/boe_downloads/2020_general.xlsx \
    --list-sheets  # First, see what's available

python scripts/preprocess_results.py data/raw/boe_downloads/2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020
```

### 3. Output Location
The processed CSV files will be saved to:
```
data/raw/results_2020.csv
data/raw/results_2022.csv
etc.
```

## File Organization

```
data/raw/
├── boe_downloads/          ← Original Excel files (you add these)
│   ├── 2020_general.xlsx
│   └── 2022_general.xlsx
├── precincts_2020/         ← Shapefiles (already downloaded ✅)
├── precincts_2022/
├── results_2020.csv        ← Processed results (created by script)
└── results_2022.csv
```

## Important Notes

- ⚠️ These Excel files can be **large** (5-50 MB each)
- ⚠️ They are **NOT tracked by git** (see `.gitignore`)
- ✅ Keep them here as a **backup** of your source data
- ✅ You can **reprocess** them anytime if needed

## Alternative: Use Absolute Path

If you prefer to keep the files elsewhere (e.g., `~/Documents/franklin_county_data/`), you can reference them with absolute paths:

```bash
python scripts/preprocess_results.py ~/Documents/franklin_county_data/2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020
```

The script works with any path - just keep your files organized!

## Download Links

- **Election Results:** https://vote.franklincountyohio.gov/election-info/
- **Archive Results:** Check the year-specific pages on the BOE website
- **Ohio Secretary of State:** https://www.ohiosos.gov/elections/election-results-and-data/ (backup source)

## Questions?

See `docs/PREPROCESSING_RESULTS.md` for detailed extraction instructions.

