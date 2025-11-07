# Shapefile Download Summary

## ✅ Task Complete

All Franklin County, Ohio precinct shapefiles have been successfully downloaded from the official Franklin County Board of Elections website.

## What Was Downloaded

**Source**: https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files  
**Download Date**: November 7, 2025  
**Total Size**: ~3.7 MB

### Years Included (10 years)

| Year | Files | Status | Notes |
|------|-------|--------|-------|
| 2024 | 5 | ✅ Complete | Base year (General Election) |
| 2022 | 5 | ✅ Complete | General Election |
| 2020 | 5 | ✅ Complete | General Election |
| 2018 | 5 | ✅ Complete | General Election |
| 2016 | 5 | ✅ Complete | General Election |
| 2014 | 5 | ✅ Complete | General Election |
| 2012 | 4 | ✅ Complete | General Election |
| 2010 | 4 | ✅ Complete | General Election |
| 2008 | 3 | ✅ Complete | No .prj file available |
| 2006 | 3 | ✅ Complete | No .prj file available |

### File Organization

```
data/raw/
├── precincts_2024/
│   ├── Voting_Precinct.shp
│   ├── Voting_Precinct.shx
│   ├── Voting_Precinct.dbf
│   ├── Voting_Precinct.prj
│   └── Voting_Precinct.cpg
├── precincts_2022/
│   └── [same structure]
...
└── precincts_2006/
    ├── Voting_Precinct.shp
    ├── Voting_Precinct.shx
    └── Voting_Precinct.dbf
```

## Scripts Created

1. **`scripts/download_shapefiles_curl.sh`**
   - Downloads all shapefiles from Board of Elections
   - Uses `curl` for reliable downloads
   - Handles years 2006-2024
   - Can be re-run to update files

2. **`scripts/inspect_shapefiles.py`**
   - Inspects shapefile structure and field names
   - Shows CRS information
   - Displays sample data
   - Run after installing dependencies

## Documentation Created

1. **`DATA_SOURCES.md`**
   - Complete data source documentation
   - Attribution and licensing
   - Instructions for obtaining election results
   - Contact information for data providers

2. **`data/raw/README.md`**
   - Guide to downloaded shapefiles
   - Next steps for users
   - Re-download instructions

## Configuration Updated

Updated `config/project.yaml`:
- ✅ Paths point to downloaded shapefiles
- ✅ All years 2006-2024 configured
- ✅ Source URL documented
- ℹ️ Note: Precinct ID field names need verification (run `inspect_shapefiles.py`)

## Next Steps for Users

### Before Running Pipeline

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Inspect field names**:
   ```bash
   python scripts/inspect_shapefiles.py
   ```

3. **Update `config/project.yaml`** with correct ID field names

4. **Download election results** from:
   https://vote.franklincountyohio.gov/election-info/

5. **Create CSV files**: `data/raw/results_YYYY.csv` with format:
   ```csv
   PRECINCT,D_votes,R_votes
   A001,450,350
   ```

### Running the Pipeline

```bash
python -m src.cli init                 # Validate setup
python -m src.cli harmonize-all        # Harmonize all years
python -m src.cli metrics              # Compute metrics
python -m src.cli maps 2024 D_share    # Create visualizations
```

## Re-downloading

To update shapefiles if Board of Elections publishes new versions:

```bash
./scripts/download_shapefiles_curl.sh
```

## Technical Details

- **Download Method**: `curl` with follow redirects (-L)
- **Error Handling**: Graceful failures with warnings
- **Naming Convention**: All files renamed to `Voting_Precinct.*` for consistency
- **CRS**: Original CRS preserved, auto-reprojected to EPSG:3734 by pipeline

## Data Attribution

**Source**: Franklin County Board of Elections  
**Address**: 1700 Morse Rd, Columbus, OH 43229  
**Phone**: 614-525-3100  
**Website**: https://vote.franklincountyohio.gov  
**License**: Public domain (government data)

## Verification

To verify downloads:
```bash
# Count files per year
for year in 2024 2022 2020 2018 2016 2014 2012 2010 2008 2006; do
    echo "$year: $(ls data/raw/precincts_$year/ | wc -l) files"
done

# Check total size
du -sh data/raw
```

Expected: ~3.7 MB total

---

**Status**: ✅ Complete - Ready for election results data
