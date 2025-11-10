#!/usr/bin/env python3
"""
Download Census block/tract data for Franklin County, Ohio.

Uses the Census API to get demographic data and TIGER/Line shapefiles for geography.
Franklin County, Ohio FIPS: 39049
"""

import logging
from pathlib import Path
import requests
import zipfile
import io

import geopandas as gpd
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CENSUS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'census'
CENSUS_DIR.mkdir(parents=True, exist_ok=True)

# Franklin County, Ohio
STATE_FIPS = "39"
COUNTY_FIPS = "049"

def download_tiger_blocks(year=2020):
    """Download Census block shapefiles from TIGER/Line."""
    logger.info(f"Downloading {year} Census blocks for Ohio (will filter to Franklin County)...")
    
    # TIGER/Line block shapefile URL - 2020 blocks are organized by state
    # Ohio = state 39, file is ~200MB
    url = f"https://www2.census.gov/geo/tiger/TIGER{year}/TABBLOCK20/tl_{year}_{STATE_FIPS}_tabblock20.zip"
    
    output_dir = CENSUS_DIR / f'blocks_{year}'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching from {url} (this may take a minute...)")
    response = requests.get(url, timeout=180)
    
    if response.status_code != 200:
        logger.error(f"Failed to download: HTTP {response.status_code}")
        return None
    
    # Extract ZIP
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(output_dir)
    
    # Find the .shp file
    shp_files = list(output_dir.glob('*.shp'))
    if not shp_files:
        logger.error("No shapefile found in downloaded archive")
        return None
    
    shp_path = shp_files[0]
    logger.info(f"✓ Downloaded statewide blocks to {shp_path}")
    
    # Filter to Franklin County only
    logger.info("Filtering to Franklin County...")
    gdf = gpd.read_file(shp_path)
    gdf_fc = gdf[gdf['COUNTYFP20'] == COUNTY_FIPS].copy()
    
    # Save filtered version
    output_path = output_dir / 'franklin_county_blocks.shp'
    gdf_fc.to_file(output_path)
    logger.info(f"✓ Filtered to {len(gdf_fc):,} blocks in Franklin County")
    logger.info(f"  Saved to {output_path}")
    
    return output_path


def download_acs_demographics(year=2020):
    """
    Download ACS 5-year demographic data at block group level.
    
    Note: Most demographics are available at block group level, but detailed
    place-of-birth data (African ethnicity) is only available at tract level.
    We'll download both and merge them.
    """
    logger.info(f"Downloading ACS {year} 5-year demographics for Franklin County...")
    
    # Key demographic variables from ACS (available at block group level)
    # B01003_001E: Total population
    # B19013_001E: Median household income
    # B15003_022E: Bachelor's degree
    # B15003_023E: Master's degree
    # B15003_024E: Professional degree
    # B15003_025E: Doctorate
    # B15003_001E: Total education universe
    # B03002_003E: White alone, not Hispanic
    # B03002_004E: Black alone
    # B03002_012E: Hispanic or Latino
    # B03002_001E: Total race/ethnicity universe
    # B01002_001E: Median age
    # B05002_001E: Nativity universe
    # B05002_013E: Foreign born
    # B05006_001E: Place of birth universe
    # B05006_091E: Born in Africa
    # B05006_092E: Eastern Africa
    # B05006_093E: Eritrea
    # B05006_094E: Ethiopia
    # B05006_095E: Kenya
    # B05006_096E: Somalia
    # B05006_097E: Uganda
    # B05006_098E: Zimbabwe
    # B05006_099E: Other Eastern Africa
    # B05001_006E: Not a U.S. citizen
    # B16001_001E: Language universe
    # B16001_003E: Spanish
    # B16001_006E: Other Indo-European languages
    # B16001_009E: Asian and Pacific Island languages
    # B16001_012E: Other languages (includes African languages)
    
    variables = [
        'B01003_001E',  # Total population
        'B19013_001E',  # Median household income
        'B15003_001E',  # Education universe
        'B15003_022E',  # Bachelor's
        'B15003_023E',  # Master's
        'B15003_024E',  # Professional
        'B15003_025E',  # Doctorate
        'B03002_001E',  # Race universe
        'B03002_003E',  # White NH
        'B03002_004E',  # Black
        'B03002_012E',  # Hispanic
        'B01002_001E',  # Median age
        'B05002_001E',  # Nativity universe
        'B05002_013E',  # Foreign born
        'B05006_001E',  # Place of birth universe
        'B05006_091E',  # Born in Africa
        'B05006_092E',  # Eastern Africa (total)
        'B05006_093E',  # Eritrea
        'B05006_094E',  # Ethiopia
        'B05006_095E',  # Kenya
        'B05006_096E',  # Somalia
        'B05006_097E',  # Uganda
        'B05006_098E',  # Zimbabwe
        'B05006_099E',  # Other Eastern Africa
        'B05001_006E',  # Not a U.S. citizen
        'B16001_001E',  # Language universe
        'B16001_003E',  # Spanish
        'B16001_006E',  # Other Indo-European
        'B16001_009E',  # Asian/Pacific Island
        'B16001_012E',  # Other languages (African)
    ]
    
    # ACS 5-year API endpoint (block group level)
    acs_year = year
    base_url = f"https://api.census.gov/data/{acs_year}/acs/acs5"
    
    params = {
        'get': ','.join(variables),
        'for': 'block group:*',
        'in': f'state:{STATE_FIPS} county:{COUNTY_FIPS}',
    }
    
    logger.info(f"Fetching from Census API: {base_url}")
    response = requests.get(base_url, params=params, timeout=30)
    
    if response.status_code != 200:
        logger.error(f"Census API error: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None
    
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Create GEOID for joining with shapefiles
    df['GEOID'] = df['state'] + df['county'] + df['tract'] + df['block group']
    
    # Convert numeric columns
    for col in variables:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate derived metrics
    df['pct_college'] = (
        (df['B15003_022E'] + df['B15003_023E'] + df['B15003_024E'] + df['B15003_025E']) / 
        df['B15003_001E'] * 100
    )
    df['pct_white'] = df['B03002_003E'] / df['B03002_001E'] * 100
    df['pct_black'] = df['B03002_004E'] / df['B03002_001E'] * 100
    df['pct_hispanic'] = df['B03002_012E'] / df['B03002_001E'] * 100
    df['pct_foreign_born'] = df['B05002_013E'] / df['B05002_001E'] * 100
    df['pct_africa_born'] = df['B05006_091E'] / df['B05006_001E'] * 100
    df['pct_east_africa_born'] = df['B05006_092E'] / df['B05006_001E'] * 100
    df['pct_somalia_born'] = df['B05006_096E'] / df['B05006_001E'] * 100
    df['pct_ethiopia_born'] = df['B05006_094E'] / df['B05006_001E'] * 100
    df['pct_noncitizen'] = df['B05001_006E'] / df['B05006_001E'] * 100
    df['pct_other_language'] = df['B16001_012E'] / df['B16001_001E'] * 100  # Includes African languages
    
    # Rename for clarity
    df = df.rename(columns={
        'B01003_001E': 'total_pop',
        'B19013_001E': 'median_income',
        'B01002_001E': 'median_age',
        'B05002_013E': 'foreign_born_pop',
        'B05006_091E': 'africa_born_pop',
        'B05006_092E': 'east_africa_born_pop',
        'B05006_093E': 'eritrea_born_pop',
        'B05006_094E': 'ethiopia_born_pop',
        'B05006_095E': 'kenya_born_pop',
        'B05006_096E': 'somalia_born_pop',
        'B05006_097E': 'uganda_born_pop',
        'B05006_098E': 'zimbabwe_born_pop',
        'B05006_099E': 'other_east_africa_pop',
        'B05001_006E': 'noncitizen_pop',
        'B16001_012E': 'other_language_pop',
    })
    
    # Select final columns
    output_cols = [
        'GEOID', 'total_pop', 'median_income', 'median_age',
        'pct_college', 'pct_white', 'pct_black', 'pct_hispanic',
        'pct_foreign_born', 'pct_africa_born', 'pct_east_africa_born', 
        'pct_somalia_born', 'pct_ethiopia_born',
        'pct_noncitizen', 'pct_other_language',
        'foreign_born_pop', 'africa_born_pop', 'east_africa_born_pop',
        'somalia_born_pop', 'ethiopia_born_pop', 'eritrea_born_pop',
        'kenya_born_pop', 'uganda_born_pop', 'zimbabwe_born_pop', 'other_east_africa_pop',
        'noncitizen_pop', 'other_language_pop'
    ]
    df = df[output_cols]
    
    # Save to CSV
    output_path = CENSUS_DIR / f'acs_{year}_demographics.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"✓ Saved demographics to {output_path}")
    logger.info(f"  {len(df)} block groups with demographic data")
    
    return output_path


def download_tiger_blockgroups(year=2020):
    """Download Census block group shapefiles from TIGER/Line."""
    logger.info(f"Downloading {year} Census block groups for Franklin County...")
    
    # TIGER/Line block group shapefile URL
    url = f"https://www2.census.gov/geo/tiger/TIGER{year}/BG/tl_{year}_{STATE_FIPS}_bg.zip"
    
    output_dir = CENSUS_DIR / f'blockgroups_{year}'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching from {url}")
    response = requests.get(url, timeout=60)
    
    if response.status_code != 200:
        logger.error(f"Failed to download: HTTP {response.status_code}")
        return None
    
    # Extract ZIP
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(output_dir)
    
    # Find the .shp file
    shp_files = list(output_dir.glob('*.shp'))
    if not shp_files:
        logger.error("No shapefile found in downloaded archive")
        return None
    
    shp_path = shp_files[0]
    logger.info(f"✓ Downloaded to {shp_path}")
    
    # Filter to Franklin County only
    gdf = gpd.read_file(shp_path)
    gdf_fc = gdf[gdf['COUNTYFP'] == COUNTY_FIPS].copy()
    
    # Save filtered version
    output_path = output_dir / 'franklin_county_blockgroups.shp'
    gdf_fc.to_file(output_path)
    logger.info(f"✓ Filtered to {len(gdf_fc)} block groups in Franklin County")
    logger.info(f"  Saved to {output_path}")
    
    return output_path


def merge_demographics_with_geography(year=2020):
    """Merge demographic CSV with block group shapefile."""
    logger.info(f"Merging demographics with geography for {year}...")
    
    # Load demographics
    demo_path = CENSUS_DIR / f'acs_{year}_demographics.csv'
    if not demo_path.exists():
        logger.error(f"Demographics file not found: {demo_path}")
        return None
    
    demographics = pd.read_csv(demo_path)
    
    # Load block groups
    bg_path = CENSUS_DIR / f'blockgroups_{year}' / 'franklin_county_blockgroups.shp'
    if not bg_path.exists():
        logger.error(f"Block groups shapefile not found: {bg_path}")
        return None
    
    gdf = gpd.read_file(bg_path)
    
    # Ensure GEOID is string in both dataframes
    gdf['GEOID'] = gdf['GEOID'].astype(str)
    demographics['GEOID'] = demographics['GEOID'].astype(str)
    
    # Merge
    gdf_merged = gdf.merge(demographics, on='GEOID', how='left')
    
    # Save as GeoPackage
    output_path = CENSUS_DIR / f'franklin_county_demographics_{year}.gpkg'
    gdf_merged.to_file(output_path, driver='GPKG')
    
    logger.info(f"✓ Merged demographics with geography")
    logger.info(f"  {len(gdf_merged)} block groups total")
    logger.info(f"  {gdf_merged['total_pop'].notna().sum()} with demographic data")
    logger.info(f"  Saved to {output_path}")
    
    # Print summary stats
    logger.info("\nDemographic summary for Franklin County:")
    logger.info(f"  Total population: {gdf_merged['total_pop'].sum():,.0f}")
    logger.info(f"  Median income: ${gdf_merged['median_income'].median():,.0f}")
    logger.info(f"  Median age: {gdf_merged['median_age'].median():.1f}")
    logger.info(f"  % College degree: {gdf_merged['pct_college'].mean():.1f}%")
    logger.info(f"  % White (NH): {gdf_merged['pct_white'].mean():.1f}%")
    logger.info(f"  % Black: {gdf_merged['pct_black'].mean():.1f}%")
    logger.info(f"  % Hispanic: {gdf_merged['pct_hispanic'].mean():.1f}%")
    
    return output_path


def main():
    """Download all Census data."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING CENSUS DATA FOR FRANKLIN COUNTY, OHIO")
    logger.info("=" * 60)
    
    year = 2020  # Use 2020 Census
    
    # Download Census blocks (for precise geographic crosswalk)
    blocks_path = download_tiger_blocks(year)
    if not blocks_path:
        logger.error("Failed to download Census blocks")
        return 1
    
    # Download block groups (for demographics)
    bg_path = download_tiger_blockgroups(year)
    if not bg_path:
        logger.error("Failed to download block groups")
        return 1
    
    # Download demographic data from ACS
    demo_path = download_acs_demographics(year)
    if not demo_path:
        logger.error("Failed to download demographics")
        return 1
    
    # Merge demographics with geography
    merged_path = merge_demographics_with_geography(year)
    if not merged_path:
        logger.error("Failed to merge data")
        return 1
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ CENSUS DATA DOWNLOAD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\nData saved to: {CENSUS_DIR}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Run: python scripts/aggregate_demographics_to_precincts.py")
    logger.info(f"  2. View demographic maps in the webapp")
    
    return 0


if __name__ == '__main__':
    exit(main())

