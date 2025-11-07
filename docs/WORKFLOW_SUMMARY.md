# Complete Workflow: Franklin County Partisan Shift Analysis

## Overview

This document provides the **complete end-to-end workflow** for analyzing precinct-level partisan shifts in Franklin County, Ohio from 2006 to present.

## Step-by-Step Process

### Phase 1: Data Collection ✅ COMPLETE

**1.1 Download Shapefiles** ✅
```bash
./scripts/download_shapefiles.sh
```

**Result:** 13 years of precinct boundary shapefiles (2006-2025) in `data/raw/precincts_YYYY/`

**Status:** ✅ Done - shapefiles downloaded and organized

---

### Phase 2: Results Preprocessing ⚠️ YOUR TASK

**2.1 Download Election Results**

Go to: https://vote.franklincountyohio.gov/election-info/

Download the official results Excel files for each election year:
- 2006 General
- 2007 General (if available)
- 2008 General
- 2010 General
- 2012 General
- 2014 General
- 2016 General
- 2018 General
- 2020 General
- 2022 General
- 2023 General (if available)
- 2024 General (or latest)

Save to a working directory (e.g., `~/Downloads/franklin_results/`)

**2.2 Choose Your Analysis Race**

**Recommended for partisan shift analysis:**

| Year | Race to Use | Candidates (Example) |
|------|-------------|---------------------|
| 2006 | Governor | Strickland (D) vs Blackwell (R) |
| 2008 | **Presidential** | Obama (D) vs McCain (R) |
| 2010 | Governor | Kasich (R) vs Strickland (D) |
| 2012 | **Presidential** | Obama (D) vs Romney (R) |
| 2014 | Governor | Kasich (R) vs FitzGerald (D) |
| 2016 | **Presidential** | Clinton (D) vs Trump (R) |
| 2018 | Governor | Cordray (D) vs DeWine (R) |
| 2020 | **Presidential** | Biden (D) vs Trump (R) |
| 2022 | Governor | Whaley (D) vs DeWine (R) |
| 2024 | **Presidential** | Harris (D) vs Trump (R) |

**2.3 Extract Race Data**

For each year, run the preprocessing script:

```bash
# Example: 2020 Presidential
python scripts/preprocess_results.py ~/Downloads/franklin_results/2020_general.xlsx \
    --list-sheets  # First, see what sheets are available

python scripts/preprocess_results.py ~/Downloads/franklin_results/2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020
```

This creates: `data/raw/results_2020.csv`

**Repeat for all years.**

**Alternative:** Manually preprocess in Excel (see `docs/PREPROCESSING_RESULTS.md`)

**2.4 Verify Output Format**

Each CSV should look like:
```csv
PRECINCT,D_votes,R_votes
01A,450,350
01B,520,480
02A,612,445
...
```

---

### Phase 3: Configuration ⚠️ VERIFY

**3.1 Check Shapefile ID Fields**

Each shapefile may use different field names for precinct IDs. Check them:

```bash
# Install GDAL if needed
pip install gdal  # or: sudo apt-get install gdal-bin

# Check each year
for year in 2006 2007 2008 2010 2012 2014 2016 2018 2020 2022 2023 2025; do
    echo "=== $year ==="
    ogrinfo -al -so data/raw/precincts_$year/*.shp | grep "Column\|Field" | head -5
done
```

Look for field names like: `PRECINCT`, `PREC_ID`, `PRECINCT_ID`, `NAME`

**3.2 Update Configuration**

Edit `config/project.yaml` and update the `id_fields` section with the actual field names:

```yaml
id_fields:
  2025: "PRECINCT"      # ← Update if different
  2023: "PRECINCT"      # ← Update if different
  2022: "PRECINCT"      # ← Update if different
  # ... etc
```

Also verify the `results_csv` paths match your extracted files.

---

### Phase 4: Run the Pipeline 🚀

**4.1 Initialize & Validate**

```bash
# Activate virtual environment if not already active
source .venv/bin/activate

# Validate everything
python -m src.cli init
```

This checks:
- ✅ Config file is valid
- ✅ All shapefile paths exist
- ✅ All results CSV paths exist
- ✅ Dependencies installed
- ✅ Output directories created

**4.2 Harmonize All Years**

```bash
python -m src.cli harmonize-all
```

This will:
1. For each historical year:
   - Load shapefile and results
   - Build spatial crosswalk to 2025 base geography
   - Reallocate votes proportionally
   - Save harmonized GeoPackage layer
2. Progress bars show status
3. Takes ~5-15 minutes per year

**Output:** `data/processed/harmonized.gpkg` with layers for each year

**4.3 Compute Metrics**

```bash
python -m src.cli metrics
```

Calculates:
- Democratic two-party share by precinct by year
- Year-over-year partisan swings
- Swings vs. baseline years (e.g., vs. 2008)
- Turnout and turnout changes
- County-wide aggregates

**Output:**
- `data/processed/timeseries_per_precinct.csv` (long format)
- `data/processed/timeseries_per_precinct_wide.csv` (wide format)
- `data/processed/county_aggregates.csv`

**4.4 Create Visualizations**

```bash
# Map 2024 Democratic share
python -m src.cli maps 2025 D_share

# Map partisan swing from 2008 to 2024
python -m src.cli maps 2025 swing_vs_2008

# Map turnout
python -m src.cli maps 2025 turnout
```

**Output:**
- `data/processed/maps/*.png` (static images)
- `data/processed/interactive/*.html` (interactive maps - open in browser)

**4.5 View Summary**

```bash
python -m src.cli summary
```

Shows county-wide results by year in terminal.

---

### Phase 5: Analysis & Interpretation 📊

**5.1 Open Outputs**

**GeoPackage (for QGIS/ArcGIS):**
```
data/processed/harmonized.gpkg
```
- Layers: `yr_2006_on_2025`, `yr_2008_on_2025`, etc.
- Each has 2025 geometry with that year's votes

**Time Series (for Excel/Python/R):**
```
data/processed/timeseries_per_precinct.csv
data/processed/timeseries_per_precinct_wide.csv
```

**Interactive Maps (for web browser):**
```
data/processed/interactive/*.html
```

**5.2 Example Analysis in Python**

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load time series
df = pd.read_csv('data/processed/timeseries_per_precinct.csv')

# Filter to one interesting precinct
precinct = df[df['PREC_ID'] == 'SOME_PRECINCT_ID']

# Plot partisan trend
precinct.plot(x='year', y='D_share', kind='line', marker='o')
plt.title('Precinct Partisan Shift Over Time')
plt.ylabel('Democratic Two-Party Share')
plt.ylim(0, 1)
plt.axhline(0.5, color='gray', linestyle='--')
plt.show()
```

**5.3 County-Wide Trends**

```python
# Load county aggregates
county = pd.read_csv('data/processed/county_aggregates.csv')

# Plot county trend
county.plot(x='year', y='D_share', kind='line', marker='o', figsize=(12, 6))
plt.title('Franklin County Partisan Trend')
plt.ylabel('Democratic Two-Party Share')
plt.axhline(0.5, color='gray', linestyle='--')
plt.show()
```

**5.4 Identify Largest Shifts**

```python
# Load wide format
df_wide = pd.read_csv('data/processed/timeseries_per_precinct_wide.csv')

# Calculate total shift 2008 to 2024
df_wide['shift_2008_2024'] = df_wide['D_share_2024'] - df_wide['D_share_2008']

# Top 10 Democratic shifts
print("Top 10 precincts shifting Democratic:")
print(df_wide.nlargest(10, 'shift_2008_2024')[['PREC_ID', 'shift_2008_2024']])

# Top 10 Republican shifts
print("\nTop 10 precincts shifting Republican:")
print(df_wide.nsmallest(10, 'shift_2008_2024')[['PREC_ID', 'shift_2008_2024']])
```

---

## Alternative: Run Everything at Once

If you have all results CSVs ready:

```bash
./scripts/run_pipeline.sh
```

This runs init → harmonize-all → metrics → maps → summary in sequence.

---

## Troubleshooting

### "Column 'PRECINCT' not found"
**Fix:** Update `id_fields` in `config/project.yaml` with correct field names from shapefiles.

### "File not found: results_2020.csv"
**Fix:** Run preprocessing script to extract that year's data, or comment out that year in config.

### "CRS mismatch error"
**Fix:** The pipeline should auto-reproject. If issues persist, check that `.prj` files exist for shapefiles.

### "Low coverage warning" (< 98%)
**Info:** Some precincts don't overlap perfectly between years. This is expected - the pipeline still works.

### Very slow performance
**Fix:** Process years individually instead of `harmonize-all`:
```bash
python -m src.cli harmonize 2008
python -m src.cli harmonize 2012
# etc.
```

---

## Expected Timeline

| Task | Time |
|------|------|
| Download results from BOE | 30 min |
| Preprocess all years | 1-2 hours |
| Verify configuration | 15 min |
| Run harmonization (13 years) | 1-3 hours |
| Compute metrics | 5 min |
| Create visualizations | 10 min |
| **Total** | **3-6 hours** |

Most of this is hands-off processing time!

---

## What You Get

After completion, you'll have:

1. ✅ **Harmonized precinct boundaries** across 13+ years
2. ✅ **Time-series data** showing partisan evolution for every precinct
3. ✅ **Swing calculations** showing which areas shifted most
4. ✅ **Interactive maps** for exploration
5. ✅ **County-wide trends** 
6. ✅ **Publication-ready datasets** for further analysis

---

## Next Steps

- **Academic Analysis:** Use the CSVs in your statistical software
- **Journalism:** Use the interactive maps for storytelling
- **Campaign Strategy:** Identify swing precincts and trends
- **Further Research:** Add demographic data, economic indicators, etc.

---

## Questions?

See the documentation:
- `README.md` - General overview
- `docs/QUICKSTART.md` - Quick start guide
- `docs/PREPROCESSING_RESULTS.md` - Detailed preprocessing help
- `SHAPEFILES_DOWNLOADED.md` - Shapefile information

Or open an issue on GitHub!

