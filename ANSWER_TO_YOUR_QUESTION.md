# Answer: How to Handle Multi-Sheet Election Results Files

## Your Question

> "The election results files on the board of elections website are typically multipage spreadsheets with many different races and issues. Is the best way to proceed for me to preprocess these files into the format you mention (precinct, D votes, R votes) for one given race?"

## Answer: YES! ✅

**You are absolutely correct.** Here's what you need to know:

## Why Preprocessing is Necessary

Franklin County BOE results files are complex:
- ✅ Multiple Excel sheets (Presidential, Senate, House, Judges, etc.)
- ✅ Multiple candidates per race (including third parties)
- ✅ Summary rows (totals, absentee, provisional)
- ✅ Complex formatting with headers and metadata

The harmonization pipeline needs **simple, clean data**:
```csv
PRECINCT,D_votes,R_votes
01A,450,350
02B,520,480
```

## Solution: I've Created Tools to Help!

### Automated Preprocessing Script ⭐

I've created `scripts/preprocess_results.py` to automate this for you:

```bash
# Step 1: See what races are available
python scripts/preprocess_results.py 2020_general.xlsx --list-sheets

# Step 2: Extract the race you want
python scripts/preprocess_results.py 2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020
```

**Result:** `data/raw/results_2020.csv` in the correct format!

## Which Race Should You Choose?

For **partisan shift analysis**, I recommend:

### Presidential Years (2008, 2012, 2016, 2020, 2024)
→ Extract **Presidential** race
- Highest turnout
- Best for partisan trends
- Most complete data

### Midterm Years (2006, 2010, 2014, 2018, 2022)
→ Extract **Governor** race
- Next best for partisan measure
- Complements presidential data

### Strategy
Use a **mix of Presidential + Governor** to get complete time series:
- 2006: Governor
- 2008: Presidential ⭐
- 2010: Governor
- 2012: Presidential ⭐
- 2014: Governor
- 2016: Presidential ⭐
- 2018: Governor
- 2020: Presidential ⭐
- 2022: Governor
- 2024: Presidential ⭐

This gives you a consistent top-of-ticket partisan measure!

## Step-by-Step Workflow

### 1. Download Results from BOE
Visit: https://vote.franklincountyohio.gov/election-info/

Download Excel files for each year you want.

### 2. Run Preprocessing Script

```bash
# For each year:
python scripts/preprocess_results.py <file.xlsx> \
    --sheet "Presidential" \
    --dem-candidate "<Name>" \
    --rep-candidate "<Name>" \
    --year <YYYY>
```

### 3. Verify Output

Check that `data/raw/results_YYYY.csv` looks correct:
```bash
head data/raw/results_2020.csv
```

### 4. Repeat for All Years

Do this for 2006, 2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024, etc.

### 5. Run the Pipeline

Once all results CSVs are ready:
```bash
python -m src.cli harmonize-all
python -m src.cli metrics
python -m src.cli maps 2025 D_share
```

## Alternative: Manual Preprocessing

If you prefer to do it manually or the script doesn't work:

1. Open Excel file
2. Navigate to race sheet (e.g., "Presidential")
3. Copy precinct column + D candidate column + R candidate column
4. Paste into new sheet
5. Rename headers: `PRECINCT`, `D_votes`, `R_votes`
6. Remove total rows
7. Save as CSV: `results_YYYY.csv`

## Documentation Created

I've created extensive documentation to help:

📄 **Main Documentation:**
- `docs/PREPROCESSING_RESULTS.md` - **Detailed guide on extraction**
- `docs/WORKFLOW_SUMMARY.md` - Complete end-to-end workflow
- `QUICKREF.md` - One-page quick reference

📄 **Tools Created:**
- `scripts/preprocess_results.py` - **Automated extraction script**
- `scripts/download_shapefiles.sh` - Download shapefiles (already done)
- `scripts/run_pipeline.sh` - Run complete pipeline

## Quick Example

```bash
# Download 2020 results from BOE website
# Save to ~/Downloads/2020_general.xlsx

# Extract Presidential race
python scripts/preprocess_results.py ~/Downloads/2020_general.xlsx \
    --sheet "Presidential" \
    --dem-candidate "Biden" \
    --rep-candidate "Trump" \
    --year 2020

# Output: data/raw/results_2020.csv
# Format: PRECINCT,D_votes,R_votes

# Repeat for other years, then:
python -m src.cli harmonize-all
```

## Summary

✅ **Yes, you need to preprocess** - one race at a time  
✅ **I've created an automated script** to make this easy  
✅ **Choose Presidential or Governor races** for best results  
✅ **Extract all years**, then run the pipeline  
✅ **Complete documentation** in `docs/` folder  

## Next Steps

1. Download BOE results Excel files for each year
2. Use `scripts/preprocess_results.py` to extract your chosen race
3. Verify the output CSVs
4. Run the harmonization pipeline
5. Analyze 19 years of partisan shifts!

---

**The shapefiles are already downloaded. Once you preprocess the results, you'll be ready to run the complete analysis!** 🎉

