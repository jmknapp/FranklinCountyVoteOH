#!/usr/bin/env python3
"""
Aggregate Census block group demographics to precinct level.

Uses spatial overlay to determine which block groups intersect with each precinct,
then calculates population-weighted averages for demographic variables.
"""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CENSUS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'census'
PRECINCTS_DIR = PROJECT_ROOT / 'data' / 'raw'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'processed'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def aggregate_demographics_to_precincts(precinct_shp, census_gpkg, output_csv, year_label='2025'):
    """
    Aggregate Census demographics from block groups to precincts.
    
    Args:
        precinct_shp: Path to precinct shapefile
        census_gpkg: Path to Census demographics geopackage
        output_csv: Path to save output CSV
        year_label: Label for the precinct year
    """
    logger.info(f"Loading {year_label} precincts from {precinct_shp}")
    precincts = gpd.read_file(precinct_shp)
    
    # Standardize CRS
    if precincts.crs and precincts.crs.to_string() not in ['EPSG:4326', 'EPSG:3734', 'EPSG:3735', 'EPSG:3747']:
        logger.info(f"Converting precincts from {precincts.crs} to EPSG:3735")
        precincts = precincts.to_crs('EPSG:3735')
    elif not precincts.crs:
        logger.warning("Precinct shapefile has no CRS, assuming EPSG:3735")
        precincts = precincts.set_crs('EPSG:3735')
    
    logger.info(f"Loading Census demographics from {census_gpkg}")
    demographics = gpd.read_file(census_gpkg)
    
    # Ensure same CRS
    if demographics.crs.to_string() != precincts.crs.to_string():
        logger.info(f"Converting demographics from {demographics.crs} to {precincts.crs}")
        demographics = demographics.to_crs(precincts.crs)
    
    logger.info(f"Loaded {len(precincts)} precincts and {len(demographics)} block groups")
    
    # Spatial overlay to find intersections
    logger.info("Computing spatial overlay (this may take a moment)...")
    overlay = gpd.overlay(precincts, demographics, how='intersection')
    
    # Calculate intersection areas
    overlay['intersection_area'] = overlay.geometry.area
    
    # For each precinct-blockgroup intersection, calculate the fraction of the blockgroup's population
    # that should be assigned to the precinct
    overlay['pop_weight'] = overlay['intersection_area'] / overlay.groupby('GEOID')['intersection_area'].transform('sum')
    
    # Calculate weighted demographics for each precinct
    demographic_cols = ['total_pop', 'median_income', 'median_age', 
                        'pct_college', 'pct_white', 'pct_black', 'pct_hispanic']
    
    # For median income and median age, we'll use population-weighted average
    # For percentages, we'll calculate from weighted totals
    
    results = []
    
    # Identify precinct ID column (could be NAME, PRECINCT, etc.)
    precinct_id_col = None
    for col in ['NAME', 'PRECINCT', 'PRECINCTID']:
        if col in precincts.columns:
            precinct_id_col = col
            break
    
    if not precinct_id_col:
        logger.error("Could not identify precinct ID column")
        return None
    
    logger.info(f"Using '{precinct_id_col}' as precinct identifier")
    
    for precinct_id in precincts[precinct_id_col].unique():
        precinct_data = overlay[overlay[precinct_id_col] == precinct_id].copy()
        
        if len(precinct_data) == 0:
            # No demographic data for this precinct
            results.append({
                'PRECINCT': precinct_id,
                'total_pop': np.nan,
                'median_income': np.nan,
                'median_age': np.nan,
                'pct_college': np.nan,
                'pct_white': np.nan,
                'pct_black': np.nan,
                'pct_hispanic': np.nan,
            })
            continue
        
        # Calculate weighted population for each intersection
        precinct_data['weighted_pop'] = precinct_data['total_pop'] * precinct_data['pop_weight']
        
        total_pop = precinct_data['weighted_pop'].sum()
        
        if total_pop == 0:
            results.append({
                'PRECINCT': precinct_id,
                'total_pop': 0,
                'median_income': np.nan,
                'median_age': np.nan,
                'pct_college': np.nan,
                'pct_white': np.nan,
                'pct_black': np.nan,
                'pct_hispanic': np.nan,
            })
            continue
        
        # Population-weighted average for median income and age
        precinct_data['weighted_income'] = precinct_data['median_income'] * precinct_data['weighted_pop']
        precinct_data['weighted_age'] = precinct_data['median_age'] * precinct_data['weighted_pop']
        
        avg_income = precinct_data['weighted_income'].sum() / total_pop
        avg_age = precinct_data['weighted_age'].sum() / total_pop
        
        # For percentages, calculate from raw counts
        # pct_college is already a percentage in our data, so we need to back-calculate the counts
        # Actually, looking at the download script, we have the raw counts in B15003_* variables
        # But we only saved the percentages. Let's just use population-weighted averages for now.
        
        precinct_data['weighted_pct_college'] = precinct_data['pct_college'] * precinct_data['weighted_pop']
        precinct_data['weighted_pct_white'] = precinct_data['pct_white'] * precinct_data['weighted_pop']
        precinct_data['weighted_pct_black'] = precinct_data['pct_black'] * precinct_data['weighted_pop']
        precinct_data['weighted_pct_hispanic'] = precinct_data['pct_hispanic'] * precinct_data['weighted_pop']
        
        avg_pct_college = precinct_data['weighted_pct_college'].sum() / total_pop
        avg_pct_white = precinct_data['weighted_pct_white'].sum() / total_pop
        avg_pct_black = precinct_data['weighted_pct_black'].sum() / total_pop
        avg_pct_hispanic = precinct_data['weighted_pct_hispanic'].sum() / total_pop
        
        results.append({
            'PRECINCT': precinct_id,
            'total_pop': total_pop,
            'median_income': avg_income,
            'median_age': avg_age,
            'pct_college': avg_pct_college,
            'pct_white': avg_pct_white,
            'pct_black': avg_pct_black,
            'pct_hispanic': avg_pct_hispanic,
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save to CSV
    results_df.to_csv(output_csv, index=False)
    logger.info(f"✓ Saved aggregated demographics to {output_csv}")
    logger.info(f"  {len(results_df)} precincts with demographic data")
    logger.info(f"  {results_df['total_pop'].notna().sum()} precincts with population data")
    
    # Print summary statistics
    logger.info("\nPrecinct-level demographic summary:")
    logger.info(f"  Total population: {results_df['total_pop'].sum():,.0f}")
    logger.info(f"  Median income range: ${results_df['median_income'].min():,.0f} - ${results_df['median_income'].max():,.0f}")
    logger.info(f"  Median age range: {results_df['median_age'].min():.1f} - {results_df['median_age'].max():.1f}")
    logger.info(f"  College % range: {results_df['pct_college'].min():.1f}% - {results_df['pct_college'].max():.1f}%")
    
    return output_csv


def main():
    """Aggregate demographics for all available precinct years."""
    logger.info("=" * 60)
    logger.info("AGGREGATING CENSUS DEMOGRAPHICS TO PRECINCTS")
    logger.info("=" * 60)
    
    census_gpkg = CENSUS_DIR / 'franklin_county_demographics_2020.gpkg'
    
    if not census_gpkg.exists():
        logger.error(f"Census demographics file not found: {census_gpkg}")
        logger.error("Run: python scripts/download_census_data.py")
        return 1
    
    # Process 2025 precincts (most recent)
    precinct_2025 = PRECINCTS_DIR / 'precincts_2025' / 'VotingPrecinct.shp'
    
    if precinct_2025.exists():
        logger.info("\n--- Processing 2025 Precincts ---")
        output_2025 = OUTPUT_DIR / 'demographics_by_precinct_2025.csv'
        aggregate_demographics_to_precincts(
            precinct_2025, 
            census_gpkg, 
            output_2025,
            year_label='2025'
        )
    else:
        logger.warning(f"2025 precinct shapefile not found: {precinct_2025}")
    
    # Optionally process other years
    # Could add 2024, 2023, etc. if needed
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ DEMOGRAPHICS AGGREGATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\nData saved to: {OUTPUT_DIR}")
    logger.info(f"\nNext step:")
    logger.info(f"  View demographic correlations in the webapp")
    
    return 0


if __name__ == '__main__':
    exit(main())

