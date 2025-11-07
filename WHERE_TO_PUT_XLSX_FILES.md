# Where to Put Excel Files

## Quick Answer

**Put your downloaded BOE Excel files here:**

```
data/raw/boe_downloads/
```

## Directory Structure

```
data/raw/
├── boe_downloads/               ← PUT EXCEL FILES HERE 📁
│   ├── 2006_general.xlsx
│   ├── 2008_general.xlsx
│   ├── 2010_general.xlsx
│   ├── 2012_general.xlsx
│   ├── 2014_general.xlsx
│   ├── 2016_general.xlsx
│   ├── 2018_general.xlsx
│   ├── 2020_general.xlsx
│   ├── 2022_general.xlsx
│   └── 2024_general.xlsx
│
├── precincts_2006/              ← Shapefiles (already here ✅)
├── precincts_2008/
├── ...
│
├── results_2006.csv             ← Processed CSVs (created by script)
├── results_2008.csv
└── ...
```

## Why This Location?

✅ **Keeps originals separate** from processed files  
✅ **Clearly organized** - source vs output  
✅ **Easy to reprocess** if needed  
✅ **Git ignores** the large files (saves space)  
✅ **Well documented** with README in directory

## Usage Example

### 1. Download Files
Go to https://vote.franklincountyohio.gov/election-info/ and download to:
```
data/raw/boe_downloads/2020_general.xlsx
```

### 2. Process with Script
```bash
python scripts/preprocess_results.py data/raw/boe_downloads/2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020
```

### 3. Output Created
```
data/raw/results_2020.csv  ← This is what the pipeline uses
```

## Alternative: Use Any Location

If you prefer to keep files elsewhere, that works too!

```bash
# Files in Documents folder
python scripts/preprocess_results.py ~/Documents/2020_general.xlsx \
    --sheet "Presidential" --dem-candidate "Biden" --rep-candidate "Trump" --year 2020

# Files in Downloads folder
python scripts/preprocess_results.py ~/Downloads/boe_files/2020_general.xlsx \
    --sheet "Presidential" --dem-candidate "Biden" --rep-candidate "Trump" --year 2020
```

The script accepts any path - use whatever organization works for you!

## Recommended File Names

**Format:** `YYYY_<type>.xlsx`

Good examples:
- ✅ `2020_general.xlsx`
- ✅ `2020_primary.xlsx`
- ✅ `2023_municipal.xlsx`

Avoid:
- ❌ `nov_2020.xlsx` (not sortable)
- ❌ `presidential_election.xlsx` (which year?)
- ❌ `Franklin County General Election November 2020.xlsx` (too verbose)

## Git Tracking

The `.gitignore` file excludes:
- `*.xlsx` and `*.xls` files (too large)
- Contents of `data/raw/boe_downloads/` (except README)
- All processed data files

This keeps your git repository small while preserving your local copies.

## Need More Help?

See:
- `data/raw/boe_downloads/README.md` - Full documentation for this directory
- `docs/PREPROCESSING_RESULTS.md` - Complete preprocessing guide
- `QUICKREF.md` - Quick command reference

---

**TL;DR:** Put Excel files in `data/raw/boe_downloads/` and reference them when running the preprocessing script. 📁

