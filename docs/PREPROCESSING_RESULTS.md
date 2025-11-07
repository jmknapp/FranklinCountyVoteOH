# Preprocessing Franklin County Election Results

## The Challenge

Franklin County Board of Elections election results are typically:
- **Multi-sheet Excel files** with separate tabs for different races
- **Many races per file**: Presidential, Governor, Senate, House, State Legislature, Judges, Ballot Issues, etc.
- **Complex formatting**: Headers, totals, provisional ballots, absentee votes
- **Multiple candidates**: Not just D vs R, but also third parties, write-ins

The harmonization pipeline needs **simple CSVs** with just:
```csv
PRECINCT,D_votes,R_votes
A001,450,350
A002,520,480
```

## Solution: Preprocessing

You need to **extract one race at a time** from the BOE files and create simplified CSVs.

## Which Race to Choose?

For **partisan shift analysis**, best races are:

### 1. Presidential (Recommended)
- ✅ Every 4 years (2008, 2012, 2016, 2020, 2024)
- ✅ Highest turnout
- ✅ Best for long-term partisan trends
- ✅ Most complete precinct-level data
- ⚠️ Only available in presidential years

### 2. Governor
- ✅ Every 4 years, but in midterms (2006, 2010, 2014, 2018, 2022)
- ✅ State-level partisan indicator
- ✅ Complements presidential data
- ⚠️ Slightly lower turnout than presidential

### 3. U.S. Senate
- ✅ National partisan trends
- ⚠️ Not every year (Ohio: 2006, 2010, 2012, 2016, 2018, 2022, 2024)
- ⚠️ Sometimes no race or unopposed

### 4. State House/Senate
- ✅ Local trends
- ⚠️ Many unopposed races
- ⚠️ District boundaries don't align with precincts
- ❌ Not recommended for county-wide partisan shift analysis

## Recommended Strategy

**Use a combination for complete timeline:**
- **Presidential years (2008, 2012, 2016, 2020, 2024):** Extract Presidential race
- **Midterm years (2006, 2010, 2014, 2018, 2022):** Extract Governor race
- **Odd years (2007, 2009, etc.):** May only have local races - skip or use best available

This gives you a **top-of-ticket partisan measure** for every even year.

## Automated Preprocessing Script

I've created a Python script to help: `scripts/preprocess_results.py`

### Step 1: List Available Sheets

```bash
python scripts/preprocess_results.py results_2020_general.xlsx --list-sheets
```

Output:
```
Available sheets in results_2020_general.xlsx:
  1. Presidential
  2. U.S. Senate
  3. U.S. House
  4. State Senate
  5. State House
  6. Supreme Court
  ...
```

### Step 2: Extract a Specific Race

```bash
python scripts/preprocess_results.py results_2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020
```

Output:
```
Loading: results_2020_general.xlsx
Loaded sheet: Presidential
Loaded 1247 rows, 8 columns
Using precinct column: Precinct
Using Democratic column: Joseph R. Biden (DEM)
Using Republican column: Donald J. Trump (REP)

Extracting race data...
Extracted 1141 precincts
Total D votes: 362,975
Total R votes: 281,342
D share: 56.3%

✓ Saved to: data/raw/results_2020.csv
```

### Step 3: Verify the Output

```bash
head -20 data/raw/results_2020.csv
```

Should show:
```csv
PRECINCT,D_votes,R_votes
01A,234,187
01B,412,298
...
```

## Manual Preprocessing (Alternative)

If the automated script doesn't work or you prefer manual control:

### Option A: Excel

1. Open the BOE results file
2. Go to the sheet for your chosen race (e.g., "Presidential")
3. Identify columns:
   - Precinct name/ID
   - Democratic candidate votes
   - Republican candidate votes
4. Create new sheet with just those 3 columns
5. Rename headers to: `PRECINCT`, `D_votes`, `R_votes`
6. Remove total/summary rows
7. Save as CSV: `results_YYYY.csv`

### Option B: Python/Pandas

```python
import pandas as pd

# Load specific sheet
df = pd.read_excel('results_2020.xlsx', sheet_name='Presidential')

# Extract relevant columns (adjust column names as needed)
results = df[['Precinct', 'Biden (DEM)', 'Trump (REP)']].copy()

# Rename
results.columns = ['PRECINCT', 'D_votes', 'R_votes']

# Clean
results['PRECINCT'] = results['PRECINCT'].str.strip().str.upper()
results = results[~results['PRECINCT'].str.contains('TOTAL|ABSENTEE', na=False)]

# Convert to int
results['D_votes'] = results['D_votes'].fillna(0).astype(int)
results['R_votes'] = results['R_votes'].fillna(0).astype(int)

# Save
results.to_csv('data/raw/results_2020.csv', index=False)
```

## Common Issues & Solutions

### Issue: Column names vary by year

**Solution:** The preprocessing script tries to auto-detect, but you can specify:
```bash
python scripts/preprocess_results.py input.xlsx \
    --precinct-col "Precinct Name" \
    --dem-col "Joseph R. Biden" \
    --rep-col "Donald J. Trump" \
    --year 2020
```

### Issue: Third-party candidates

**Decision:** The pipeline only uses D vs R for partisan shift analysis. This is standard practice as third parties vary significantly by race.

### Issue: Some precincts have zero votes

**Solution:** The preprocessing script automatically removes zero-vote precincts. The harmonization pipeline also handles missing precincts gracefully.

### Issue: Early/Absentee/Provisional totals

**Solution:** The preprocessing script excludes these summary rows by default. If you want to include them, use `--include-totals`.

### Issue: Special elections or primaries

**Decision:** For partisan shift analysis, use **general elections only**. Primaries show intra-party dynamics, not overall partisan lean.

## Workflow Summary

1. **Download results** from Franklin County BOE website
2. **Choose race** (Presidential for even years, Governor for midterms)
3. **Run preprocessing script:**
   ```bash
   python scripts/preprocess_results.py <file.xlsx> \
       --sheet "Presidential" \
       --dem-candidate "<Name>" \
       --rep-candidate "<Name>" \
       --year <YYYY>
   ```
4. **Verify output:** Check `data/raw/results_YYYY.csv`
5. **Repeat for each year**
6. **Run pipeline:**
   ```bash
   python -m src.cli harmonize-all
   python -m src.cli metrics
   ```

## Example: Complete 2008-2024 Presidential Series

```bash
# 2008 Presidential
python scripts/preprocess_results.py 2008_general.xlsx \
    --sheet "Presidential" --dem-candidate "Obama" --rep-candidate "McCain" --year 2008

# 2012 Presidential
python scripts/preprocess_results.py 2012_general.xlsx \
    --sheet "Presidential" --dem-candidate "Obama" --rep-candidate "Romney" --year 2012

# 2016 Presidential
python scripts/preprocess_results.py 2016_general.xlsx \
    --sheet "Presidential" --dem-candidate "Clinton" --rep-candidate "Trump" --year 2016

# 2020 Presidential
python scripts/preprocess_results.py 2020_general.xlsx \
    --sheet "Presidential" --dem-candidate "Biden" --rep-candidate "Trump" --year 2020

# 2024 Presidential
python scripts/preprocess_results.py 2024_general.xlsx \
    --sheet "Presidential" --dem-candidate "Harris" --rep-candidate "Trump" --year 2024
```

Now you have a consistent presidential partisan series!

## Questions?

- **Which candidate name to use?** The script does partial matching, so "Biden" or "Trump" usually works
- **What about minor parties?** Exclude them - focus on D vs R for partisan shift
- **What about write-ins?** Exclude them
- **Runoff elections?** Use the general election, not the runoff
- **Unopposed races?** Skip those years or use a different race

## Next Steps

After preprocessing all years:
1. Verify CSV format matches expected structure
2. Update `config/project.yaml` if needed
3. Run: `python -m src.cli init` to validate
4. Run: `python -m src.cli harmonize-all` to process everything!

