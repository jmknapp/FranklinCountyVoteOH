#!/usr/bin/env python3
"""
Helper script to preprocess Franklin County election results.

Converts complex multi-sheet BOE results into the simple format needed
for the harmonization pipeline: PRECINCT,D_votes,R_votes

Usage:
    # Standard results file
    python scripts/preprocess_results.py input.xlsx --sheet "Presidential" --year 2020
    
    # Group detail file (for House races)
    python scripts/preprocess_results.py input_detail.xlsx --detail-file --extract-house --year 2024
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import numpy as np


def load_excel_file(filepath: str, sheet_name: str = None) -> pd.DataFrame:
    """Load Excel file and optionally a specific sheet."""
    try:
        if sheet_name:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            print(f"Loaded sheet: {sheet_name}")
        else:
            # Load first sheet by default
            df = pd.read_excel(filepath)
            print(f"Loaded first sheet")
        return df
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)


def list_sheets(filepath: str):
    """List all sheet names in an Excel file."""
    try:
        xls = pd.ExcelFile(filepath)
        print(f"\nAvailable sheets in {Path(filepath).name}:")
        for i, sheet in enumerate(xls.sheet_names, 1):
            print(f"  {i}. {sheet}")
        print()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def find_precinct_column(df: pd.DataFrame) -> str:
    """Try to identify the precinct column."""
    # Common precinct column names
    candidates = [
        'PRECINCT', 'Precinct', 'precinct',
        'PREC', 'Prec',
        'PRECINCT_ID', 'Precinct ID',
        'PRECINCT NAME', 'Precinct Name',
    ]
    
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in candidates:
            return col_str
        # Partial match
        if 'PRECINCT' in col_str.upper() or 'PREC' in col_str.upper():
            return col_str
    
    print("Warning: Could not auto-detect precinct column.")
    print("Available columns:", list(df.columns))
    return None


def find_candidate_columns(df: pd.DataFrame, d_name: str = None, r_name: str = None):
    """
    Find columns for Democratic and Republican candidates.
    
    If candidate names are provided, search for them.
    Otherwise, try to auto-detect.
    """
    columns = {col: str(col).strip() for col in df.columns}
    
    d_col = None
    r_col = None
    
    if d_name:
        # Search for Democratic candidate
        for col, col_str in columns.items():
            if d_name.lower() in col_str.lower():
                d_col = col
                break
    
    if r_name:
        # Search for Republican candidate
        for col, col_str in columns.items():
            if r_name.lower() in col_str.lower():
                r_col = col
                break
    
    # Auto-detection fallback
    if not d_col or not r_col:
        print("\nAvailable columns:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        print("\nCouldn't auto-detect candidate columns.")
        print("Please specify --dem-candidate and --rep-candidate")
    
    return d_col, r_col


def fix_precinct_name(name: str) -> str:
    """Fix precinct names to use zero-padded numbers (e.g., 'BEXLEY 1-A' -> 'BEXLEY 01-A')."""
    # Match pattern: [WORDS] [DIGIT(S)]-[LETTER(S)]
    # Handles both single words (BEXLEY) and multi-word (UPPER ARLINGTON)
    match = re.match(r'^(.+?)\s+(\d{1,2})-([A-Z]+)$', name)
    if match:
        prefix, num, suffix = match.groups()
        return f"{prefix} {int(num):02d}-{suffix}"
    return name


def extract_race_data(
    df: pd.DataFrame,
    precinct_col: str,
    d_col: str,
    r_col: str,
    skip_totals: bool = True,
    fix_names: bool = True
) -> pd.DataFrame:
    """Extract precinct-level D/R votes for a specific race."""
    
    # Select relevant columns
    try:
        result = df[[precinct_col, d_col, r_col]].copy()
    except KeyError as e:
        print(f"Error: Column not found: {e}")
        sys.exit(1)
    
    # Rename to standard format
    result.columns = ['PRECINCT', 'D_votes', 'R_votes']
    
    # Clean precinct names
    result['PRECINCT'] = result['PRECINCT'].astype(str).str.strip().str.upper()
    
    # Remove summary rows (TOTAL, COUNTY TOTAL, etc.)
    if skip_totals:
        total_mask = result['PRECINCT'].str.contains(
            'TOTAL|ABSENTEE|PROVISIONAL|CUMULATIVE|NAN',
            case=False,
            na=False
        )
        result = result[~total_mask]
    
    # Convert votes to numeric
    result['D_votes'] = pd.to_numeric(result['D_votes'], errors='coerce').fillna(0).astype(int)
    result['R_votes'] = pd.to_numeric(result['R_votes'], errors='coerce').fillna(0).astype(int)
    
    # Remove rows with no votes
    result = result[(result['D_votes'] > 0) | (result['R_votes'] > 0)]
    
    # Fix precinct names (zero-padding)
    if fix_names:
        result['PRECINCT'] = result['PRECINCT'].apply(fix_precinct_name)
    
    # Sort by precinct
    result = result.sort_values('PRECINCT').reset_index(drop=True)
    
    return result


def extract_house_races_from_detail(filepath: str, year: int) -> dict:
    """
    Extract House races from a Franklin County 'group detail' results file.
    
    The detail file splits precincts by State Legislative districts, which allows
    us to properly separate Congressional District results.
    
    Returns:
        dict: {cd_name: DataFrame} with results for each Congressional District
    """
    print(f"\nProcessing group detail file for House races...")
    
    # Load the file
    xls = pd.ExcelFile(filepath)
    print(f"Found sheets: {xls.sheet_names}")
    
    # Load first sheet with proper skipping
    df = pd.read_excel(filepath, sheet_name=xls.sheet_names[0], skiprows=2)
    print(f"Loaded {len(df)} rows")
    
    # Find precinct column (typically 3rd column after skiprows)
    precinct_col = df.columns[2]
    print(f"Using precinct column: {precinct_col}")
    
    # Define Congressional races in Franklin County
    # These will need to be updated for different years
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
    
    print("\nIdentified House races:")
    for cd, candidates in house_races.items():
        print(f"  {cd}: {candidates['D']} vs {candidates['R']}")
    
    # Process each row to determine which CD it belongs to
    results = []
    
    for idx, row in df.iterrows():
        precinct = row[precinct_col]
        if pd.isna(precinct) or 'TOTAL' in str(precinct).upper():
            continue
        
        # Check votes for each CD
        cd_votes = {}
        for cd, candidates in house_races.items():
            d_col = candidates['D']
            r_col = candidates['R']
            
            d_votes = row.get(d_col, 0) if d_col in df.columns else 0
            r_votes = row.get(r_col, 0) if r_col in df.columns else 0
            total_votes = d_votes + r_votes
            
            if total_votes > 0:
                cd_votes[cd] = {
                    'D_votes': d_votes,
                    'R_votes': r_votes,
                    'total': total_votes
                }
        
        # Assign to CD with most votes
        if cd_votes:
            best_cd = max(cd_votes.items(), key=lambda x: x[1]['total'])[0]
            results.append({
                'PRECINCT': str(precinct).strip().upper(),
                'CD': best_cd,
                'D_votes': cd_votes[best_cd]['D_votes'],
                'R_votes': cd_votes[best_cd]['R_votes']
            })
    
    results_df = pd.DataFrame(results)
    
    # Aggregate by precinct and CD (in case of multiple State House districts)
    grouped = results_df.groupby(['PRECINCT', 'CD'], as_index=False).agg({
        'D_votes': 'sum',
        'R_votes': 'sum'
    })
    
    # Fix precinct names
    grouped['PRECINCT'] = grouped['PRECINCT'].apply(fix_precinct_name)
    
    # Split into separate DataFrames by CD
    cd_results = {}
    for cd in house_races.keys():
        cd_df = grouped[grouped['CD'] == cd][['PRECINCT', 'D_votes', 'R_votes']].copy()
        cd_df = cd_df.sort_values('PRECINCT').reset_index(drop=True)
        cd_results[cd] = cd_df
    
    # Print summary
    print("\n=== EXTRACTION SUMMARY ===")
    for cd, cd_df in cd_results.items():
        total_d = cd_df['D_votes'].sum()
        total_r = cd_df['R_votes'].sum()
        d_pct = 100 * total_d / (total_d + total_r)
        print(f"{cd}: {len(cd_df)} precincts, D={d_pct:.1f}%, R={100-d_pct:.1f}%")
    
    return cd_results


def save_house_results(cd_results: dict, year: int, output_dir: Path = None):
    """Save House race results for each Congressional District."""
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for cd, cd_df in cd_results.items():
        cd_num = cd.replace('CD-', '')
        output_path = output_dir / f"results_{year}_house_cd{cd_num}.csv"
        cd_df.to_csv(output_path, index=False)
        saved_files.append(output_path)
        print(f"✓ Saved {cd}: {output_path}")
    
    return saved_files


def main():
    parser = argparse.ArgumentParser(
        description='Preprocess Franklin County election results for harmonization pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available sheets
  python scripts/preprocess_results.py results_2020.xlsx --list-sheets
  
  # Extract Presidential race
  python scripts/preprocess_results.py results_2020.xlsx \\
      --sheet "Presidential" \\
      --dem-candidate "Biden" \\
      --rep-candidate "Trump" \\
      --year 2020
  
  # Extract House races from group detail file
  python scripts/preprocess_results.py results_2024_detail.xlsx \\
      --detail-file \\
      --extract-house \\
      --year 2024
  
  # Extract specific Congressional District
  python scripts/preprocess_results.py results_2024_detail.xlsx \\
      --detail-file \\
      --extract-house \\
      --cd CD-03 \\
      --year 2024
        """
    )
    
    parser.add_argument('input_file', help='Input Excel file from BOE')
    parser.add_argument('--sheet', help='Sheet name or index (default: first sheet)')
    parser.add_argument('--year', type=int, required=False, help='Election year (for output filename)')
    
    parser.add_argument('--list-sheets', action='store_true', 
                       help='List all sheets in the Excel file and exit')
    
    # Detail file options
    parser.add_argument('--detail-file', action='store_true',
                       help='Input is a "group detail" file (splits by State Legislative district)')
    parser.add_argument('--extract-house', action='store_true',
                       help='Extract House races from detail file (requires --detail-file)')
    parser.add_argument('--cd', help='Extract specific Congressional District (e.g., CD-03, CD-15)')
    
    # Column specification
    parser.add_argument('--precinct-col', help='Precinct column name (auto-detect if not specified)')
    parser.add_argument('--dem-col', '--dem-candidate', 
                       help='Democratic candidate column name or partial name')
    parser.add_argument('--rep-col', '--rep-candidate',
                       help='Republican candidate column name or partial name')
    
    # Output options
    parser.add_argument('--output', '-o', help='Output CSV file (default: data/raw/results_YEAR.csv)')
    parser.add_argument('--output-dir', help='Output directory for multiple files (default: data/raw)')
    parser.add_argument('--include-totals', action='store_true',
                       help='Include total/summary rows (default: exclude)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)
    
    # List sheets if requested
    if args.list_sheets:
        list_sheets(args.input_file)
        return
    
    # Handle detail file with House race extraction
    if args.detail_file and args.extract_house:
        if not args.year:
            print("Error: --year is required when extracting House races")
            sys.exit(1)
        
        # Extract House races
        cd_results = extract_house_races_from_detail(args.input_file, args.year)
        
        # Filter to specific CD if requested
        if args.cd:
            if args.cd not in cd_results:
                print(f"Error: {args.cd} not found. Available: {list(cd_results.keys())}")
                sys.exit(1)
            cd_results = {args.cd: cd_results[args.cd]}
        
        # Save results
        output_dir = Path(args.output_dir) if args.output_dir else Path("data/raw")
        saved_files = save_house_results(cd_results, args.year, output_dir)
        
        print(f"\n✓ Extracted {len(saved_files)} Congressional District(s)")
        print("\nNext steps:")
        print("  Run harmonization for each CD separately:")
        for cd, cd_df in cd_results.items():
            cd_num = cd.replace('CD-', '')
            print(f"    python -m src.cli harmonize --results-csv data/raw/results_{args.year}_house_cd{cd_num}.csv \\")
            print(f"        --race-name 'House {cd}' --output data/processed/{cd.lower()}_harmonized.csv")
        
        return
    
    # Standard processing for non-detail files
    # Load data
    print(f"\nLoading: {args.input_file}")
    df = load_excel_file(args.input_file, args.sheet)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Find precinct column
    precinct_col = args.precinct_col or find_precinct_column(df)
    if not precinct_col:
        print("\nError: Could not identify precinct column.")
        print("Please specify --precinct-col")
        sys.exit(1)
    print(f"Using precinct column: {precinct_col}")
    
    # Find candidate columns
    d_col, r_col = find_candidate_columns(df, args.dem_col, args.rep_col)
    
    if not d_col or not r_col:
        sys.exit(1)
    
    print(f"Using Democratic column: {d_col}")
    print(f"Using Republican column: {r_col}")
    
    # Extract data
    print("\nExtracting race data...")
    result = extract_race_data(
        df,
        precinct_col,
        d_col,
        r_col,
        skip_totals=not args.include_totals
    )
    
    print(f"Extracted {len(result)} precincts")
    print(f"Total D votes: {result['D_votes'].sum():,}")
    print(f"Total R votes: {result['R_votes'].sum():,}")
    print(f"D share: {result['D_votes'].sum() / (result['D_votes'].sum() + result['R_votes'].sum()):.1%}")
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    elif args.year:
        output_path = Path(f"data/raw/results_{args.year}.csv")
    else:
        output_path = Path("data/raw/results_processed.csv")
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    result.to_csv(output_path, index=False)
    print(f"\n✓ Saved to: {output_path}")
    
    # Show preview
    print("\nPreview:")
    print(result.head(10).to_string(index=False))
    
    if len(result) > 10:
        print(f"... ({len(result) - 10} more rows)")


if __name__ == '__main__':
    main()

