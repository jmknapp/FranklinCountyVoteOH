# ✅ Franklin County Shapefiles Successfully Downloaded

## Summary

All available Franklin County, Ohio precinct shapefiles have been downloaded from the [Franklin County Board of Elections](https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files) and organized into the project structure.

## What Was Downloaded

**13 years** of precinct boundary shapefiles spanning **2006-2025**:

```
data/raw/
├── precincts_2006/  (572 KB)  - Precincts_G06.shp
├── precincts_2007/  (1.5 MB)  - Precincts_G07.shp
├── precincts_2008/  (1.2 MB)  - Precincts_08.shp
├── precincts_2009/  (1.5 MB)  - Precincts_P09.shp
├── precincts_2010/  (100 KB)  - Precincts_G10.shp
├── precincts_2012/  (100 KB)  - Precincts_G12.shp
├── precincts_2014/  (116 KB)  - Precincts_G14.shp
├── precincts_2016/  (116 KB)  - Voting-Precincts-G16.shp
├── precincts_2018/  (116 KB)  - Voting-Precincts-G18.shp
├── precincts_2020/  (116 KB)  - Voting-Precincts-G20.shp
├── precincts_2022/  (104 KB)  - Voting-Precincts-G22.shp
├── precincts_2023/  (1.4 MB)  - Voting_Precinct.shp
└── precincts_2025/  (1.4 MB)  - Voting_Precinct.shp
```

**Total Downloaded:** ~6.6 MB of shapefile data

## Configuration Updated

The project configuration (`config/project.yaml`) has been updated to:
- **Base year:** 2025 (latest available)
- **All shapefile paths:** Point to correct files
- **Years configured:** 2006-2025 (13 years)
- **CRS:** EPSG:3734 (NAD83 / Ohio South)

## Next Steps to Run the Pipeline

### 1. Verify Precinct ID Fields

Each shapefile may use different field names for precinct IDs. Inspect them:

```bash
# Install GDAL if needed
sudo apt-get install gdal-bin  # Linux
brew install gdal              # Mac

# Check field names for each year
ogrinfo -al -so data/raw/precincts_2025/Voting_Precinct.shp | grep -A 20 "Layer name"
```

Common field names: `PRECINCT`, `PREC_ID`, `PRECINCT_ID`, `NAME`

Update `id_fields` in `config/project.yaml` with the correct names.

### 2. Download Election Results

You need election results CSVs with Democratic and Republican vote counts by precinct.

**Sources:**
- [Franklin County BOE - Election Results](https://vote.franklincountyohio.gov/election-info/)
- [Ohio Secretary of State - Election Results](https://www.ohiosos.gov/elections/election-results-and-data/)

**Required format:**
```csv
PRECINCT,D_votes,R_votes
A001,450,350
A002,520,480
...
```

Save as:
```
data/raw/results_2006.csv
data/raw/results_2007.csv
...
data/raw/results_2025.csv
```

### 3. Run the Pipeline

Once you have results CSVs:

```bash
# Activate virtual environment
source .venv/bin/activate

# Initialize and validate
python -m src.cli init

# Harmonize all years to 2025 base geography
python -m src.cli harmonize-all

# Compute partisan metrics
python -m src.cli metrics

# Create visualizations
python -m src.cli maps 2025 D_share
python -m src.cli maps 2025 swing_vs_2008

# View summary
python -m src.cli summary
```

### 4. Or Run Everything at Once

```bash
./scripts/run_pipeline.sh
```

## Automated Re-download Script

If shapefiles are updated in the future, re-run:

```bash
./scripts/download_shapefiles.sh
```

This will download the latest versions from the Franklin County BOE website.

## File Structure Created

```
fcvote/
├── config/
│   └── project.yaml          ← Updated with actual shapefile paths
├── data/
│   └── raw/
│       ├── precincts_YYYY/   ← 13 directories with shapefiles
│       └── README_SHAPEFILES.md  ← Detailed shapefile documentation
├── scripts/
│   ├── download_shapefiles.sh    ← Automated download script
│   └── run_pipeline.sh           ← Complete pipeline runner
└── [All other project files]
```

## Documentation

- **Shapefile Details:** `data/raw/README_SHAPEFILES.md`
- **Project Overview:** `README.md`
- **Quick Start Guide:** `docs/QUICKSTART.md`
- **This Summary:** `SHAPEFILES_DOWNLOADED.md`

## What's Still Needed

✅ Shapefiles - **DONE**  
⚠️ Election Results CSVs - **YOU NEED TO ADD THESE**  
⚠️ Verify Precinct ID Fields - **UPDATE CONFIG IF NEEDED**

## Questions?

- **Shapefile Source:** https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files
- **Election Results:** https://vote.franklincountyohio.gov/election-info/
- **Franklin County BOE:** 614-525-3100

---

**Ready to proceed!** Once you add election results CSVs, the pipeline can harmonize 19 years of precinct-level election data across changing boundaries.

