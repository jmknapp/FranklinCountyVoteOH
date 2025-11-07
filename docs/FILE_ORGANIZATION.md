# File Organization Guide

## Complete Directory Structure

```
fcvote/
├── config/
│   └── project.yaml                    # Configuration (update as needed)
│
├── data/
│   ├── raw/
│   │   ├── boe_downloads/              # 📁 PUT YOUR EXCEL FILES HERE
│   │   │   ├── README.md               #    Instructions
│   │   │   ├── 2006_general.xlsx      #    ← You download these
│   │   │   ├── 2008_general.xlsx
│   │   │   ├── 2010_general.xlsx
│   │   │   └── ...
│   │   │
│   │   ├── precincts_2006/             # ✅ Shapefiles (already done)
│   │   ├── precincts_2008/
│   │   ├── ...
│   │   ├── precincts_2025/
│   │   │
│   │   ├── results_2006.csv            # ← Script creates these
│   │   ├── results_2008.csv
│   │   └── ...
│   │
│   ├── interim/
│   │   └── crosswalks/                 # Spatial crosswalks (created by pipeline)
│   │       ├── crosswalk_2006_to_2025.csv
│   │       └── ...
│   │
│   ├── processed/                      # Final outputs
│   │   ├── harmonized.gpkg            # GeoPackage (for QGIS)
│   │   ├── timeseries_per_precinct.csv
│   │   ├── county_aggregates.csv
│   │   ├── maps/                       # Static PNG maps
│   │   └── interactive/                # Interactive HTML maps
│   │
│   └── examples/                       # Synthetic demo data
│
├── docs/                               # Documentation
│   ├── QUICKSTART.md
│   ├── PREPROCESSING_RESULTS.md
│   ├── WORKFLOW_SUMMARY.md
│   └── FILE_ORGANIZATION.md           # This file
│
├── scripts/
│   ├── download_shapefiles.sh         # Downloads shapefiles (done)
│   ├── preprocess_results.py          # Extracts races from Excel
│   └── run_pipeline.sh                # Runs complete pipeline
│
├── src/                                # Source code
│   ├── cli.py
│   ├── crosswalk.py
│   ├── harmonize.py
│   ├── metrics.py
│   ├── visualize.py
│   └── ...
│
└── tests/                              # Test suite
```

## File Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│ 1. YOU DOWNLOAD                                     │
│    https://vote.franklincountyohio.gov/            │
│    ↓                                                 │
│    data/raw/boe_downloads/2020_general.xlsx        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 2. YOU RUN PREPROCESSING SCRIPT                     │
│    python scripts/preprocess_results.py ...         │
│    ↓                                                 │
│    data/raw/results_2020.csv                        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 3. PIPELINE USES                                     │
│    - data/raw/precincts_2020/*.shp  (shapefile)     │
│    - data/raw/results_2020.csv      (your CSV)      │
│    ↓                                                 │
│    ffs harmonize-all                                │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 4. PIPELINE CREATES                                  │
│    - data/interim/crosswalks/...                     │
│    - data/processed/harmonized.gpkg                  │
│    - data/processed/timeseries_per_precinct.csv      │
│    - data/processed/maps/*.png                       │
│    - data/processed/interactive/*.html               │
└─────────────────────────────────────────────────────┘
```

## What Goes Where

### Input Files (You Provide)

| File Type | Location | Purpose |
|-----------|----------|---------|
| **Excel files** | `data/raw/boe_downloads/*.xlsx` | Original BOE downloads |
| Shapefiles | `data/raw/precincts_YYYY/` | Already downloaded ✅ |

### Intermediate Files (Script Creates)

| File Type | Location | Purpose |
|-----------|----------|---------|
| **Results CSVs** | `data/raw/results_YYYY.csv` | Extracted race data |
| Crosswalks | `data/interim/crosswalks/` | Spatial mappings |

### Output Files (Pipeline Creates)

| File Type | Location | Purpose |
|-----------|----------|---------|
| GeoPackage | `data/processed/harmonized.gpkg` | For QGIS/GIS software |
| Time series | `data/processed/timeseries_*.csv` | For analysis |
| Static maps | `data/processed/maps/*.png` | For reports |
| Interactive maps | `data/processed/interactive/*.html` | For web/exploration |

## Quick Reference

### Where to put Excel files?
```
data/raw/boe_downloads/2020_general.xlsx
```

### How to process them?
```bash
python scripts/preprocess_results.py data/raw/boe_downloads/2020_general.xlsx \
    --sheet "Presidential" --dem-candidate "Biden" --rep-candidate "Trump" --year 2020
```

### Where is the output?
```
data/raw/results_2020.csv
```

### What does the pipeline use?
```
data/raw/precincts_2020/*.shp  +  data/raw/results_2020.csv
```

## Storage Considerations

### Typical File Sizes

| Item | Size Range | Git Tracked? |
|------|------------|--------------|
| Excel files (each) | 5-50 MB | ❌ No (.gitignore) |
| Shapefiles (each year) | 100 KB - 1.5 MB | ❌ No (.gitignore) |
| Results CSVs (each) | 10-50 KB | ❌ No (.gitignore) |
| GeoPackage output | 10-100 MB | ❌ No (.gitignore) |
| Maps (each) | 500 KB - 5 MB | ❌ No (.gitignore) |
| **Source code** | 100 KB | ✅ Yes |
| **Documentation** | 200 KB | ✅ Yes |

### Total Storage

- **Excel files:** ~200-500 MB (13 years)
- **Shapefiles:** ~7 MB (13 years) ✅ Downloaded
- **Processed outputs:** ~100-200 MB
- **Total project:** ~300-700 MB

## Tips

### ✅ Good Practices

- Keep original Excel files as backup
- Use consistent naming: `YYYY_general.xlsx`
- One race per year for consistency
- Document which race you used

### ❌ Avoid

- Don't commit large files to git
- Don't delete original Excel files
- Don't mix different races (Presidential + Senate)
- Don't rename preprocessed CSVs

## Need Help?

| Question | See Document |
|----------|--------------|
| Where to put files? | `WHERE_TO_PUT_XLSX_FILES.md` |
| How to extract races? | `docs/PREPROCESSING_RESULTS.md` |
| Complete workflow? | `docs/WORKFLOW_SUMMARY.md` |
| Quick commands? | `QUICKREF.md` |

---

**Summary:** Put Excel files in `data/raw/boe_downloads/`, process them to create CSVs in `data/raw/`, then run the pipeline. All outputs go to `data/processed/`. 📁

