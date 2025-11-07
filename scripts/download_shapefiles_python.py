#!/usr/bin/env python3
"""
Better shapefile downloader using Python requests with proper headers.
"""

import requests
from pathlib import Path
import time

BASE_URL = "https://vote.franklincountyohio.gov"

# UUIDs for shapefile components by year
# Format: {year: {filename: uuid}}
SHAPEFILES = {
    "2025": {
        "Voting_Precinct.cpg": "8d0f697c-9599-42a8-ac7c-b874c83bdc70",
        "Voting_Precinct.dbf": "65bd6003-91e0-497a-b1ba-f07c0ba5195e",
        "Voting_Precinct.prj": "33541603-81d5-4c69-8608-331117b8d62a",
        "Voting_Precinct.sbn": "0c4c0878-2fa8-42ff-a2f2-898c9f8060e0",
        "Voting_Precinct.sbx": "9514476b-8358-40e4-836c-c0ce6f76cdec",
        "Voting_Precinct.shp": "59989478-b4b8-4562-bef0-ad34d50829bd",
        "Voting_Precinct.shx": "59e6d59c-d860-4427-b796-ad1566cff87c",
    },
    "2022": {
        "Voting-Precincts-G22.cpg": "282370ad-918d-4de7-9554-ea84be112444",
        "Voting-Precincts-G22.dbf": "29c65037-35be-4bdb-82dc-f065d49bad7d",
        "Voting-Precincts-G22.prj": "18f80bff-e4da-408a-91f0-5dd27ad7a5c4",
        "Voting-Precincts-G22.sbn": "9c79889f-57a5-4d53-84e8-cea0d1c05784",
        "Voting-Precincts-G22.sbx": "1e5a0382-7ea9-4151-a0bd-0a7e45e2c50f",
        "Voting-Precincts-G22.shp": "66d06bfd-28f0-4f1b-9a1b-5e4b5aa7da49",
        "Voting-Precincts-G22.shx": "c4b60d33-e3c1-4b0c-be12-b8d79eef99ca",
    },
    "2020": {
        "Voting-Precincts-G20.cpg": "f0dc3f15-6ebb-478f-b38b-0fdc1f9ee11d",
        "Voting-Precincts-G20.dbf": "61f80e95-a37e-4ab0-9f26-8fc7ca1c9a75",
        "Voting-Precincts-G20.prj": "6acd9c88-49e4-49f5-af5f-e7fa41e6f29e",
        "Voting-Precincts-G20.sbn": "77e13f99-ffda-4a38-9c62-ba2ca0866fb5",
        "Voting-Precincts-G20.sbx": "1c7f638c-38ce-4ab8-9fcd-79dda0f36c5a",
        "Voting-Precincts-G20.shp": "d9eab30b-acb9-4b99-b652-9ec29d5e6c42",
        "Voting-Precincts-G20.shx": "f61bb4d7-41e8-4e34-934b-46e49bbb8258",
    },
}


def download_file(uuid, filename, output_path, session):
    """Download a single file using requests with proper headers."""
    url = f"{BASE_URL}/getmedia/{uuid}/{filename}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files',
    }
    
    try:
        print(f"  Downloading: {filename}...", end=" ", flush=True)
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        # Check if we got HTML (error page) instead of binary data
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            print("❌ Got HTML error page")
            return False
        
        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)
            size = len(response.content) / 1024  # KB
            print(f"✓ ({size:.1f} KB)")
            return True
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def download_year(year, data_dir="data/raw"):
    """Download all shapefiles for a specific year."""
    if year not in SHAPEFILES:
        print(f"❌ Year {year} not in shapefile database")
        return False
    
    print(f"\n{'='*60}")
    print(f"Downloading {year} shapefiles")
    print(f"{'='*60}")
    
    year_dir = Path(data_dir) / f"precincts_{year}"
    files = SHAPEFILES[year]
    
    session = requests.Session()
    success_count = 0
    
    for filename, uuid in files.items():
        output_path = year_dir / filename
        if download_file(uuid, filename, output_path, session):
            success_count += 1
        time.sleep(0.5)  # Be nice to the server
    
    print(f"\n{'='*60}")
    if success_count == len(files):
        print(f"✓ {year}: All {success_count} files downloaded successfully")
        return True
    else:
        print(f"⚠ {year}: {success_count}/{len(files)} files downloaded")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download Franklin County precinct shapefiles (Python version)"
    )
    parser.add_argument(
        'years',
        nargs='*',
        default=['2025', '2022', '2020'],
        help='Years to download (default: 2025, 2022, 2020 - the most important ones)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Download all available years (not recommended - just do the important ones)'
    )
    
    args = parser.parse_args()
    
    if args.all:
        years = list(SHAPEFILES.keys())
        print("⚠ Downloading ALL years - this will take a while...")
    else:
        years = args.years
    
    print(f"\nWill download shapefiles for: {', '.join(years)}")
    print("This will download to: data/raw/precincts_YYYY/")
    print("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    time.sleep(3)
    
    success = []
    failed = []
    
    for year in years:
        if download_year(year):
            success.append(year)
        else:
            failed.append(year)
    
    print(f"\n\n{'='*60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"✓ Successful: {', '.join(success) if success else 'none'}")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
    print(f"{'='*60}\n")
    
    if success:
        print("Next steps:")
        print("  1. Test a shapefile: python -c \"import geopandas as gpd; print(gpd.read_file('data/raw/precincts_2025/Voting_Precinct.shp'))\"")
        print("  2. Download election results for these years")
        print("  3. Run preprocessing: python scripts/preprocess_results.py ...")
    

if __name__ == '__main__':
    main()

