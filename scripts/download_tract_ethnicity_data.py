#!/usr/bin/env python3
"""
Download detailed place-of-birth/ethnicity data at Census tract level.

This data (Table B05006) is only available at tract level and higher,
not at block group level. We download it separately and will spatially
disaggregate it to precincts.
"""

import logging
import requests
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
CENSUS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'census'
STATE_FIPS = '39'  # Ohio
COUNTY_FIPS = '049'  # Franklin County


def download_tiger_tracts(year=2020):
    """Download Census tract shapefiles from TIGER/Line."""
    logger.info(f"Downloading {year} Census tracts for Franklin County...")
    
    # TIGER/Line tract shapefile URL
    url = f"https://www2.census.gov/geo/tiger/TIGER{year}/TRACT/tl_{year}_{STATE_FIPS}_tract.zip"
    
    output_dir = CENSUS_DIR / f'tracts_{year}'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching from {url}")
    response = requests.get(url, timeout=60)
    
    if response.status_code != 200:
        logger.error(f"Failed to download: HTTP {response.status_code}")
        return None
    
    # Save and extract ZIP
    zip_path = output_dir / f'tl_{year}_{STATE_FIPS}_tract.zip'
    with open(zip_path, 'wb') as f:
        f.write(response.content)
    
    logger.info(f"Extracting to {output_dir}")
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    
    # Find and load shapefile
    shp_path = output_dir / f'tl_{year}_{STATE_FIPS}_tract.shp'
    logger.info(f"✓ Downloaded to {shp_path}")
    
    # Filter to Franklin County only
    logger.info("Filtering to Franklin County...")
    gdf = gpd.read_file(shp_path)
    gdf_fc = gdf[gdf['COUNTYFP'] == COUNTY_FIPS].copy()
    
    # Save filtered version
    output_path = output_dir / 'franklin_county_tracts.shp'
    gdf_fc.to_file(output_path)
    logger.info(f"✓ Filtered to {len(gdf_fc):,} tracts in Franklin County")
    logger.info(f"  Saved to {output_path}")
    
    return output_path


def download_tract_ethnicity_data(year=2020):
    """
    Download detailed place-of-birth/ethnicity data at tract level.
    
    Table B05006: Place of Birth for the Foreign-Born Population
    This includes detailed country/region breakdowns for Africa.
    """
    logger.info(f"Downloading ACS {year} 5-year ethnicity data (tract level)...")
    
    # Place of birth variables (B05006)
    # B05006_001E: Total foreign-born population
    # B05006_091E: Africa
    # B05006_092E: Eastern Africa
    # B05006_093E: Eritrea
    # B05006_094E: Ethiopia
    # B05006_095E: Kenya
    # B05006_096E: Somalia
    # B05006_097E: Uganda
    # B05006_098E: Zimbabwe
    # B05006_099E: Other Eastern Africa
    # B05006_100E: Middle Africa (includes Congo, etc.)
    # B05006_101E: Cameroon
    # B05006_107E: Northern Africa (includes Egypt, Morocco, etc.)
    # B05006_113E: Southern Africa (includes South Africa, etc.)
    # B05006_119E: Western Africa (includes Nigeria, Ghana, Liberia, etc.)
    # B05006_120E: Ghana
    # B05006_121E: Liberia
    # B05006_122E: Nigeria
    # B05006_123E: Sierra Leone
    # B05006_124E: Other Western Africa
    
    ethnicity_vars = [
        'B05006_001E',  # Total place of birth universe
        'B05006_091E',  # Africa (total)
        'B05006_092E',  # Eastern Africa (total)
        'B05006_093E',  # Eritrea
        'B05006_094E',  # Ethiopia
        'B05006_095E',  # Kenya
        'B05006_096E',  # Somalia
        'B05006_097E',  # Uganda
        'B05006_098E',  # Zimbabwe
        'B05006_099E',  # Other Eastern Africa
        'B05006_100E',  # Middle Africa (total)
        'B05006_101E',  # Cameroon
        'B05006_107E',  # Northern Africa (total)
        'B05006_113E',  # Southern Africa (total)
        'B05006_119E',  # Western Africa (total)
        'B05006_120E',  # Ghana
        'B05006_121E',  # Liberia
        'B05006_122E',  # Nigeria
        'B05006_123E',  # Sierra Leone
        'B05006_124E',  # Other Western Africa
    ]
    
    # Also get nativity and citizenship (available at tract level)
    nativity_vars = [
        'B05002_001E',  # Nativity universe
        'B05002_013E',  # Foreign born
        'B05001_001E',  # Citizenship universe
        'B05001_006E',  # Not a U.S. citizen
    ]
    
    all_vars = ethnicity_vars + nativity_vars
    
    # ACS 5-year API endpoint (tract level)
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    
    params = {
        'get': ','.join(all_vars),
        'for': 'tract:*',
        'in': f'state:{STATE_FIPS} county:{COUNTY_FIPS}',
    }
    
    logger.info(f"Fetching from Census API: {base_url}")
    logger.info(f"  Requesting {len(all_vars)} variables for Franklin County tracts...")
    
    response = requests.get(base_url, params=params, timeout=30)
    
    if response.status_code != 200:
        logger.error(f"Census API error: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return None
    
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Create GEOID for joining with shapefiles
    df['GEOID'] = df['state'] + df['county'] + df['tract']
    
    # Convert numeric columns
    for col in all_vars:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate percentages and rename columns
    df['pct_africa_born'] = df['B05006_091E'] / df['B05006_001E'] * 100
    df['pct_east_africa_born'] = df['B05006_092E'] / df['B05006_001E'] * 100
    df['pct_somalia_born'] = df['B05006_096E'] / df['B05006_001E'] * 100
    df['pct_ethiopia_born'] = df['B05006_094E'] / df['B05006_001E'] * 100
    df['pct_nigeria_born'] = df['B05006_122E'] / df['B05006_001E'] * 100
    df['pct_west_africa_born'] = df['B05006_119E'] / df['B05006_001E'] * 100
    df['pct_foreign_born'] = df['B05002_013E'] / df['B05002_001E'] * 100
    df['pct_noncitizen'] = df['B05001_006E'] / df['B05001_001E'] * 100
    
    # Rename raw count columns for clarity
    df = df.rename(columns={
        'B05006_001E': 'pob_universe',
        'B05006_091E': 'africa_born',
        'B05006_092E': 'east_africa_born',
        'B05006_093E': 'eritrea_born',
        'B05006_094E': 'ethiopia_born',
        'B05006_095E': 'kenya_born',
        'B05006_096E': 'somalia_born',
        'B05006_097E': 'uganda_born',
        'B05006_098E': 'zimbabwe_born',
        'B05006_099E': 'other_east_africa',
        'B05006_100E': 'middle_africa_born',
        'B05006_101E': 'cameroon_born',
        'B05006_107E': 'north_africa_born',
        'B05006_113E': 'south_africa_born',
        'B05006_119E': 'west_africa_born',
        'B05006_120E': 'ghana_born',
        'B05006_121E': 'liberia_born',
        'B05006_122E': 'nigeria_born',
        'B05006_123E': 'sierra_leone_born',
        'B05006_124E': 'other_west_africa',
        'B05002_001E': 'nativity_universe',
        'B05002_013E': 'foreign_born',
        'B05001_001E': 'citizenship_universe',
        'B05001_006E': 'noncitizen',
    })
    
    # Select final columns
    output_cols = [
        'GEOID', 'pob_universe', 'nativity_universe', 'citizenship_universe',
        'africa_born', 'east_africa_born', 'west_africa_born', 'middle_africa_born',
        'north_africa_born', 'south_africa_born',
        'somalia_born', 'ethiopia_born', 'eritrea_born', 'kenya_born', 'uganda_born',
        'zimbabwe_born', 'other_east_africa',
        'nigeria_born', 'ghana_born', 'liberia_born', 'sierra_leone_born',
        'cameroon_born', 'other_west_africa',
        'foreign_born', 'noncitizen',
        'pct_africa_born', 'pct_east_africa_born', 'pct_somalia_born',
        'pct_ethiopia_born', 'pct_nigeria_born', 'pct_west_africa_born',
        'pct_foreign_born', 'pct_noncitizen'
    ]
    
    df = df[output_cols]
    
    # Save to CSV
    output_path = CENSUS_DIR / f'acs_{year}_tract_ethnicity.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"✓ Saved tract ethnicity data to {output_path}")
    logger.info(f"  {len(df)} tracts with data")
    
    # Print summary
    logger.info("\nFranklin County Ethnicity Summary (tract-level):")
    logger.info(f"  Total Africa-born: {df['africa_born'].sum():,}")
    logger.info(f"  East Africa-born: {df['east_africa_born'].sum():,}")
    logger.info(f"    Somalia: {df['somalia_born'].sum():,}")
    logger.info(f"    Ethiopia: {df['ethiopia_born'].sum():,}")
    logger.info(f"  West Africa-born: {df['west_africa_born'].sum():,}")
    logger.info(f"    Nigeria: {df['nigeria_born'].sum():,}")
    logger.info(f"    Liberia: {df['liberia_born'].sum():,}")
    logger.info(f"    Ghana: {df['ghana_born'].sum():,}")
    
    return output_path


def merge_ethnicity_with_geography(year=2020):
    """Merge ethnicity data with tract shapefile."""
    logger.info(f"Merging ethnicity data with geography for {year}...")
    
    # Load ethnicity data
    eth_path = CENSUS_DIR / f'acs_{year}_tract_ethnicity.csv'
    if not eth_path.exists():
        logger.error(f"Ethnicity file not found: {eth_path}")
        return None
    
    ethnicity = pd.read_csv(eth_path)
    
    # Load tracts
    tract_path = CENSUS_DIR / f'tracts_{year}' / 'franklin_county_tracts.shp'
    if not tract_path.exists():
        logger.error(f"Tracts shapefile not found: {tract_path}")
        return None
    
    gdf = gpd.read_file(tract_path)
    
    # Ensure GEOID is string in both dataframes
    gdf['GEOID'] = gdf['GEOID'].astype(str)
    ethnicity['GEOID'] = ethnicity['GEOID'].astype(str)
    
    # Merge
    gdf_merged = gdf.merge(ethnicity, on='GEOID', how='left')
    
    # Save as GeoPackage
    output_path = CENSUS_DIR / f'franklin_county_tract_ethnicity_{year}.gpkg'
    gdf_merged.to_file(output_path, driver='GPKG')
    
    logger.info(f"✓ Merged ethnicity data with geography")
    logger.info(f"  {len(gdf_merged)} tracts total")
    logger.info(f"  {gdf_merged['africa_born'].notna().sum()} with ethnicity data")
    logger.info(f"  Saved to {output_path}")
    
    return output_path


def main():
    """Download tract-level ethnicity data."""
    logger.info("=" * 60)
    logger.info("DOWNLOADING TRACT-LEVEL ETHNICITY DATA")
    logger.info("=" * 60)
    
    year = 2020
    
    # Download Census tracts
    tract_path = download_tiger_tracts(year)
    if not tract_path:
        logger.error("Failed to download Census tracts")
        return 1
    
    # Download ethnicity data from ACS
    eth_path = download_tract_ethnicity_data(year)
    if not eth_path:
        logger.error("Failed to download ethnicity data")
        return 1
    
    # Merge with geography
    merged_path = merge_ethnicity_with_geography(year)
    if not merged_path:
        logger.error("Failed to merge data")
        return 1
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ TRACT ETHNICITY DATA DOWNLOAD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\nData saved to: {CENSUS_DIR}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Run: python scripts/aggregate_tract_ethnicity_to_precincts.py")
    logger.info(f"  2. Analyze voting patterns by ethnicity")
    
    return 0


if __name__ == '__main__':
    exit(main())

