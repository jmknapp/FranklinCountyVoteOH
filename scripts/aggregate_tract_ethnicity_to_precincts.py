#!/usr/bin/env python3
"""
Aggregate tract-level ethnicity data to precinct level.

Uses spatial intersection and population weighting to disaggregate
tract-level data (which has coarser geography) to precinct level.
"""

import logging
import geopandas as gpd
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
CENSUS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'census'
PRECINCT_DIR = PROJECT_ROOT / 'data' / 'raw'
OUTPUT_PATH = PROJECT_ROOT / 'data' / 'processed' / 'ethnicity_by_precinct_2025.csv'


def load_precinct_shapefile():
    """Load 2025 precinct shapefile."""
    logger.info("Loading 2025 precinct shapefile...")
    
    shp_path = PRECINCT_DIR / 'precincts_2025' / 'VotingPrecinct.shp'
    if not shp_path.exists():
        logger.error(f"Precinct shapefile not found: {shp_path}")
        return None
    
    precincts = gpd.read_file(shp_path)
    
    # Ensure CRS
    if precincts.crs is None:
        precincts.set_crs('EPSG:3735', inplace=True)
    
    # Standardize to common CRS
    precincts = precincts.to_crs('EPSG:4326')
    
    # Use NAME column as precinct ID
    precincts['PRECINCT'] = precincts['NAME'].str.strip().str.upper()
    
    logger.info(f"  Loaded {len(precincts)} precincts")
    return precincts


def load_tract_ethnicity():
    """Load tract-level ethnicity data."""
    logger.info("Loading tract ethnicity data...")
    
    gpkg_path = CENSUS_DIR / 'franklin_county_tract_ethnicity_2020.gpkg'
    if not gpkg_path.exists():
        logger.error(f"Tract ethnicity file not found: {gpkg_path}")
        return None
    
    tracts = gpd.read_file(gpkg_path)
    
    # Standardize to common CRS
    tracts = tracts.to_crs('EPSG:4326')
    
    logger.info(f"  Loaded {len(tracts)} tracts")
    logger.info(f"  Total Africa-born: {tracts['africa_born'].sum():,.0f}")
    return tracts


def spatially_aggregate_to_precincts(precincts, tracts):
    """
    Aggregate tract data to precincts using spatial intersection.
    
    Method: For each precinct, find all intersecting tracts and allocate
    their populations proportional to the intersection area.
    """
    logger.info("Performing spatial intersection...")
    logger.info("  This may take a few minutes...")
    
    # Perform intersection
    intersection = gpd.overlay(precincts[['PRECINCT', 'geometry']], 
                               tracts, 
                               how='intersection',
                               keep_geom_type=False)
    
    # Calculate area of each intersection piece
    intersection['int_area'] = intersection.geometry.area
    
    # Calculate what fraction of each tract falls in each precinct
    tract_areas = tracts.set_index('GEOID').geometry.area.to_dict()
    intersection['tract_area'] = intersection['GEOID'].map(tract_areas)
    intersection['area_fraction'] = intersection['int_area'] / intersection['tract_area']
    
    logger.info(f"  Created {len(intersection)} intersection polygons")
    
    # Allocate populations proportionally
    # For each ethnicity variable, multiply by the area fraction
    ethnicity_cols = [
        'africa_born', 'east_africa_born', 'west_africa_born',
        'somalia_born', 'ethiopia_born', 'kenya_born', 'uganda_born',
        'nigeria_born', 'ghana_born', 'liberia_born',
        'foreign_born', 'noncitizen'
    ]
    
    for col in ethnicity_cols:
        intersection[f'{col}_allocated'] = intersection[col] * intersection['area_fraction']
    
    # Group by precinct and sum allocated populations
    logger.info("Aggregating to precincts...")
    
    allocated_cols = [f'{col}_allocated' for col in ethnicity_cols]
    precinct_eth = intersection.groupby('PRECINCT')[allocated_cols].sum()
    
    # Rename columns (remove _allocated suffix)
    precinct_eth.columns = [col.replace('_allocated', '') for col in precinct_eth.columns]
    
    # Also get the universe (total population in place-of-birth question)
    intersection['pob_universe_allocated'] = intersection['pob_universe'] * intersection['area_fraction']
    precinct_pob = intersection.groupby('PRECINCT')['pob_universe_allocated'].sum()
    precinct_eth['pob_universe'] = precinct_pob
    
    # Calculate percentages
    precinct_eth['pct_africa_born'] = (precinct_eth['africa_born'] / precinct_eth['pob_universe'] * 100)
    precinct_eth['pct_east_africa_born'] = (precinct_eth['east_africa_born'] / precinct_eth['pob_universe'] * 100)
    precinct_eth['pct_somalia_born'] = (precinct_eth['somalia_born'] / precinct_eth['pob_universe'] * 100)
    precinct_eth['pct_ethiopia_born'] = (precinct_eth['ethiopia_born'] / precinct_eth['pob_universe'] * 100)
    precinct_eth['pct_nigeria_born'] = (precinct_eth['nigeria_born'] / precinct_eth['pob_universe'] * 100)
    precinct_eth['pct_west_africa_born'] = (precinct_eth['west_africa_born'] / precinct_eth['pob_universe'] * 100)
    
    # Reset index to make PRECINCT a column
    precinct_eth = precinct_eth.reset_index()
    
    logger.info(f"  Aggregated to {len(precinct_eth)} precincts")
    logger.info(f"  Total Africa-born (after allocation): {precinct_eth['africa_born'].sum():,.0f}")
    
    return precinct_eth


def main():
    """Main execution."""
    logger.info("=" * 70)
    logger.info("AGGREGATING TRACT ETHNICITY DATA TO PRECINCTS")
    logger.info("=" * 70)
    logger.info("")
    
    # Load data
    precincts = load_precinct_shapefile()
    if precincts is None:
        return 1
    
    tracts = load_tract_ethnicity()
    if tracts is None:
        return 1
    
    # Aggregate to precincts
    precinct_ethnicity = spatially_aggregate_to_precincts(precincts, tracts)
    
    # Save to CSV
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    precinct_ethnicity.to_csv(OUTPUT_PATH, index=False)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✓ AGGREGATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Output saved to: {OUTPUT_PATH}")
    logger.info("")
    logger.info("Summary statistics:")
    logger.info(f"  Precincts with data: {len(precinct_ethnicity)}")
    logger.info(f"  Total Africa-born: {precinct_ethnicity['africa_born'].sum():,.0f}")
    logger.info(f"  Total Somalia-born: {precinct_ethnicity['somalia_born'].sum():,.0f}")
    logger.info(f"  Total Ethiopia-born: {precinct_ethnicity['ethiopia_born'].sum():,.0f}")
    logger.info(f"  Total Nigeria-born: {precinct_ethnicity['nigeria_born'].sum():,.0f}")
    logger.info("")
    
    # Find precincts with highest East African populations
    logger.info("Top 10 precincts by East African-born population:")
    logger.info("-" * 70)
    top_ea = precinct_ethnicity.nlargest(10, 'east_africa_born')[
        ['PRECINCT', 'east_africa_born', 'somalia_born', 'ethiopia_born', 'pct_east_africa_born']
    ]
    for idx, row in top_ea.iterrows():
        logger.info(f"  {row['PRECINCT']:<25s} {row['east_africa_born']:>6.0f} East African "
                   f"({row['somalia_born']:>5.0f} Somali, {row['ethiopia_born']:>5.0f} Ethiopian) "
                   f"= {row['pct_east_africa_born']:>4.1f}%")
    
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Merge with existing precinct demographics")
    logger.info("  2. Analyze voting patterns by African ethnicity")
    logger.info("  3. Compare African American vs African immigrant precincts")
    
    return 0


if __name__ == '__main__':
    exit(main())

