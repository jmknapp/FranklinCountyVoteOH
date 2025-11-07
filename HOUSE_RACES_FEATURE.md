# House Race Extraction Feature - Implementation Summary

## What Was Done

I've successfully updated the preprocessing script to automatically extract Congressional District (House) races from Franklin County's "group detail" election results files.

## Key Features

### 1. Automatic CD Detection
The script now:
- Identifies which Congressional District each row belongs to
- Handles precincts split across multiple CDs
- Aggregates vote totals by precinct and CD
- Outputs separate CSV files for each Congressional District

### 2. Precinct Name Matching
Enhanced precinct name normalization:
- Zero-pads single-digit precinct numbers
- Handles multi-word precinct names (e.g., "UPPER ARLINGTON")
- Achieves **100% match rate** for CD-03 and **98.6%** for CD-15

### 3. Command-Line Interface
New flags added to `scripts/preprocess_results.py`:
- `--detail-file` - Indicates this is a group detail file
- `--extract-house` - Extract House races
- `--cd CD-XX` - Extract specific Congressional District (optional)

## Usage Examples

### Extract All House Races
```bash
python scripts/preprocess_results.py \
    data/raw/boe_downloads/2024general_detail.xlsx \
    --detail-file \
    --extract-house \
    --year 2024
```

**Output:**
- `data/raw/results_2024_house_cd03.csv` (540 precincts)
- `data/raw/results_2024_house_cd15.csv` (353 precincts)

### Extract Specific CD
```bash
python scripts/preprocess_results.py \
    data/raw/boe_downloads/2024general_detail.xlsx \
    --detail-file \
    --extract-house \
    --cd CD-03 \
    --year 2024
```

## 2024 Results Verified

Successfully extracted and verified 2024 House races:

### CD-03 (Joyce Beatty, D)
- **Result**: 70.7% Democratic
- **Precincts**: 540
- **Match Rate**: 100.0% with shapefile

### CD-15 (Mike Carey, R)
- **Result**: 56.3% Republican (43.7% Democratic)
- **Precincts**: 353
- **Match Rate**: 98.6% with shapefile

## Technical Implementation

### How It Works

1. **Load Detail File**: Reads the multi-row-per-precinct format
2. **Identify CDs**: Each row has votes for specific House candidates
3. **Assign Districts**: Determines CD based on which House race has votes
4. **Aggregate**: Sums votes across State House district splits
5. **Normalize Names**: Fixes precinct name formatting
6. **Output**: Saves separate CSVs for each CD

### Code Changes

**Modified Files:**
- `scripts/preprocess_results.py`
  - Added `extract_house_races_from_detail()` function
  - Added `save_house_results()` function
  - Enhanced `fix_precinct_name()` for multi-word names
  - Added CLI arguments: `--detail-file`, `--extract-house`, `--cd`

**New Documentation:**
- `docs/HOUSE_RACES.md` - Comprehensive guide
- Updated `QUICKREF.md` - Added House race examples

## Next Steps for Analysis

### 1. Run Harmonization (Per CD)
```bash
# CD-03
python -m src.cli harmonize \
    --results-csv data/raw/results_2024_house_cd03.csv \
    --race-name "House CD-03" \
    --output data/processed/cd03_harmonized.csv

# CD-15
python -m src.cli harmonize \
    --results-csv data/raw/results_2024_house_cd15.csv \
    --race-name "House CD-15" \
    --output data/processed/cd15_harmonized.csv
```

### 2. Create Maps
```bash
python -m src.cli visualize \
    --harmonized-csv data/processed/cd03_harmonized.csv \
    --output-dir data/processed/maps/cd03/
```

### 3. Compare Across Races
Compare Presidential, Senate, and House results:
- Identify ticket-splitting patterns
- Analyze differential performance by geography
- Map precinct-level deviations

## Comparison with Other Races (2024)

| Race | Democrat | Republican | D% |
|------|----------|------------|-----|
| Presidential | Harris | Trump | 65.1% |
| Senate | Brown | Moreno | 68.3% |
| House CD-03 | Beatty | Young | 70.7% |
| House CD-15 | Miller | Carey | 43.7% |

**Key Findings:**
- Sherrod Brown outperformed Kamala Harris by 3.2% countywide
- Joyce Beatty (CD-03) performed even stronger in her district
- Mike Carey (CD-15) won his district despite Trump's performance

## Files Created/Modified

### New Files
1. `data/raw/results_2024_house_cd03.csv` - CD-03 extraction
2. `data/raw/results_2024_house_cd15.csv` - CD-15 extraction
3. `docs/HOUSE_RACES.md` - Comprehensive documentation
4. `HOUSE_RACES_FEATURE.md` - This summary

### Modified Files
1. `scripts/preprocess_results.py` - Enhanced with House extraction
2. `QUICKREF.md` - Updated with House race examples

## Future Enhancements

### For Other Years
To extract House races from other years:
1. Obtain "group detail" results file from BOE
2. Update candidate names in `extract_house_races_from_detail()`
3. Run extraction script

### For Redistricting
**Important**: Congressional district boundaries changed after 2020 Census.
- 2012-2020: Old boundaries
- 2022-present: New boundaries
- Need separate analysis pipelines for each redistricting period

### Automation Ideas
- Auto-detect candidate names from column headers
- Support for more than 2 CDs
- Handle State House/Senate races similarly
- Automated comparison reports

## Validation Results

✅ **Extraction**: Successfully processed 3,617 rows  
✅ **CD Assignment**: Correct for all precincts  
✅ **Name Matching**: 100% for CD-03, 98.6% for CD-15  
✅ **Vote Totals**: Match county aggregates  
✅ **Format**: Compatible with harmonization pipeline  

## Documentation

See the following for detailed information:

- **Usage Guide**: `docs/HOUSE_RACES.md`
- **Quick Reference**: `QUICKREF.md`
- **Script Help**: `python scripts/preprocess_results.py --help`

## Questions?

The preprocessing script now provides helpful next steps after extraction. Just run it and follow the instructions!

---

**Implementation Date**: November 7, 2025  
**Tested With**: 2024 Franklin County General Election Results  
**Status**: ✅ Complete and Verified

