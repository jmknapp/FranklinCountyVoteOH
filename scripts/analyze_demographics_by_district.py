#!/usr/bin/env python3
"""
Aggregate Census demographics by Columbus City Council district.

Uses spatial overlay to determine which Census block groups fall within each district,
then calculates population-weighted demographic summaries.
"""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CENSUS_DIR = PROJECT_ROOT / 'data' / 'raw' / 'census'
DISTRICTS_SHP = PROJECT_ROOT / 'data' / 'raw' / 'otherBoundaries' / 'CMHcc'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'processed' / 'district_analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def aggregate_demographics_by_district():
    """Aggregate Census block group demographics by City Council district."""
    logger.info("Loading Columbus City Council districts...")
    districts = gpd.read_file(DISTRICTS_SHP)
    logger.info(f"Loaded {len(districts)} districts")
    
    # Load Census demographics (block groups with demographic data)
    census_gpkg = CENSUS_DIR / 'franklin_county_demographics_2020.gpkg'
    if not census_gpkg.exists():
        raise FileNotFoundError(f"Census data not found: {census_gpkg}. Run: python scripts/download_census_data.py")
    
    logger.info("Loading Census block groups with demographics...")
    demographics = gpd.read_file(census_gpkg)
    logger.info(f"Loaded {len(demographics)} block groups")
    
    # Ensure same CRS
    if districts.crs.to_string() != demographics.crs.to_string():
        logger.info(f"Reprojecting districts from {districts.crs} to {demographics.crs}")
        districts = districts.to_crs(demographics.crs)
    
    # Spatial overlay to find which block groups intersect with each district
    logger.info("Computing spatial overlay...")
    overlay = gpd.overlay(districts, demographics, how='intersection')
    
    # Calculate intersection areas
    overlay['intersection_area'] = overlay.geometry.area
    
    # For each district-blockgroup intersection, calculate population weight
    overlay['pop_weight'] = overlay['intersection_area'] / overlay.groupby('GEOID')['intersection_area'].transform('sum')
    
    # Calculate weighted demographics for each district
    results = []
    
    for district_id in sorted(districts['DISTRICT'].unique()):
        district_data = overlay[overlay['DISTRICT'] == district_id].copy()
        
        if len(district_data) == 0:
            logger.warning(f"No demographic data for District {district_id}")
            continue
        
        # Calculate weighted population
        district_data['weighted_pop'] = district_data['total_pop'] * district_data['pop_weight']
        total_pop = district_data['weighted_pop'].sum()
        
        if total_pop == 0:
            logger.warning(f"Zero population for District {district_id}")
            continue
        
        # Population-weighted averages
        district_data['weighted_income'] = district_data['median_income'] * district_data['weighted_pop']
        district_data['weighted_age'] = district_data['median_age'] * district_data['weighted_pop']
        district_data['weighted_pct_college'] = district_data['pct_college'] * district_data['weighted_pop']
        district_data['weighted_pct_white'] = district_data['pct_white'] * district_data['weighted_pop']
        district_data['weighted_pct_black'] = district_data['pct_black'] * district_data['weighted_pop']
        district_data['weighted_pct_hispanic'] = district_data['pct_hispanic'] * district_data['weighted_pop']
        
        results.append({
            'District': f"District {district_id}",
            'district_num': district_id,
            'total_pop': int(total_pop),
            'median_income': district_data['weighted_income'].sum() / total_pop,
            'median_age': district_data['weighted_age'].sum() / total_pop,
            'pct_college': district_data['weighted_pct_college'].sum() / total_pop,
            'pct_white': district_data['weighted_pct_white'].sum() / total_pop,
            'pct_black': district_data['weighted_pct_black'].sum() / total_pop,
            'pct_hispanic': district_data['weighted_pct_hispanic'].sum() / total_pop,
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('district_num')
    
    # Save to CSV
    output_csv = OUTPUT_DIR / 'demographics_by_council_district.csv'
    results_df.to_csv(output_csv, index=False)
    logger.info(f"✓ Saved demographics to {output_csv}")
    
    # Print summary table
    logger.info("\n" + "="*80)
    logger.info("COLUMBUS CITY COUNCIL DISTRICTS - DEMOGRAPHIC SUMMARY")
    logger.info("="*80)
    
    print("\n" + results_df.to_string(index=False))
    
    logger.info("\n" + "="*80)
    logger.info("SUMMARY STATISTICS")
    logger.info("="*80)
    logger.info(f"Total population (all districts): {results_df['total_pop'].sum():,}")
    logger.info(f"Median income range: ${results_df['median_income'].min():,.0f} - ${results_df['median_income'].max():,.0f}")
    logger.info(f"% College degree range: {results_df['pct_college'].min():.1f}% - {results_df['pct_college'].max():.1f}%")
    logger.info(f"% Black range: {results_df['pct_black'].min():.1f}% - {results_df['pct_black'].max():.1f}%")
    
    return results_df


def create_visualizations(results_df):
    """Create demographic comparison charts for districts."""
    logger.info("\nCreating visualizations...")
    
    # Set style
    sns.set_style("whitegrid")
    
    # 1. Population by district
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(results_df['District'], results_df['total_pop'], color='steelblue')
    ax.set_ylabel('Population', fontsize=12)
    ax.set_title('Population by Columbus City Council District', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'district_population.png', dpi=150)
    logger.info(f"✓ Saved {OUTPUT_DIR / 'district_population.png'}")
    plt.close()
    
    # 2. Income comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(results_df['District'], results_df['median_income'], 
                   color=plt.cm.RdYlGn(results_df['median_income'] / results_df['median_income'].max()))
    ax.set_ylabel('Median Household Income ($)', fontsize=12)
    ax.set_title('Median Income by Columbus City Council District', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    ax.axhline(results_df['median_income'].mean(), color='red', linestyle='--', linewidth=2, alpha=0.7, label='City Average')
    ax.legend()
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'${int(height):,}',
                ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'district_income.png', dpi=150)
    logger.info(f"✓ Saved {OUTPUT_DIR / 'district_income.png'}")
    plt.close()
    
    # 3. Education comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(results_df['District'], results_df['pct_college'], 
                   color=plt.cm.Blues(results_df['pct_college'] / 100))
    ax.set_ylabel('% with College Degree', fontsize=12)
    ax.set_title('Educational Attainment by Columbus City Council District', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    ax.axhline(results_df['pct_college'].mean(), color='red', linestyle='--', linewidth=2, alpha=0.7, label='City Average')
    ax.legend()
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'district_education.png', dpi=150)
    logger.info(f"✓ Saved {OUTPUT_DIR / 'district_education.png'}")
    plt.close()
    
    # 4. Racial composition
    fig, ax = plt.subplots(figsize=(12, 7))
    x = range(len(results_df))
    width = 0.25
    
    ax.bar([i - width for i in x], results_df['pct_white'], width, label='White (NH)', color='lightblue')
    ax.bar([i for i in x], results_df['pct_black'], width, label='Black', color='coral')
    ax.bar([i + width for i in x], results_df['pct_hispanic'], width, label='Hispanic', color='lightgreen')
    
    ax.set_ylabel('Percentage', fontsize=12)
    ax.set_title('Racial/Ethnic Composition by Columbus City Council District', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(results_df['District'], rotation=45)
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'district_racial_composition.png', dpi=150)
    logger.info(f"✓ Saved {OUTPUT_DIR / 'district_racial_composition.png'}")
    plt.close()
    
    # 5. Comprehensive comparison heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Normalize data for heatmap (0-100 scale)
    heatmap_data = results_df[['District', 'median_income', 'median_age', 'pct_college', 'pct_white', 'pct_black', 'pct_hispanic']].copy()
    heatmap_data['median_income_norm'] = (heatmap_data['median_income'] / heatmap_data['median_income'].max() * 100).round(1)
    heatmap_data['median_age_norm'] = (heatmap_data['median_age'] / heatmap_data['median_age'].max() * 100).round(1)
    
    plot_data = heatmap_data[['District', 'median_income_norm', 'median_age_norm', 'pct_college', 'pct_white', 'pct_black', 'pct_hispanic']].set_index('District')
    plot_data.columns = ['Income\n(normalized)', 'Age\n(normalized)', '% College', '% White\n(NH)', '% Black', '% Hispanic']
    
    sns.heatmap(plot_data.T, annot=True, fmt='.1f', cmap='YlOrRd', cbar_kws={'label': 'Value'}, ax=ax)
    ax.set_title('Demographic Comparison: Columbus City Council Districts', fontsize=14, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'district_heatmap.png', dpi=150)
    logger.info(f"✓ Saved {OUTPUT_DIR / 'district_heatmap.png'}")
    plt.close()


def main():
    """Analyze demographics by City Council district."""
    logger.info("="*80)
    logger.info("COLUMBUS CITY COUNCIL DISTRICT DEMOGRAPHIC ANALYSIS")
    logger.info("="*80)
    
    results_df = aggregate_demographics_by_district()
    create_visualizations(results_df)
    
    logger.info("\n" + "="*80)
    logger.info("✓ ANALYSIS COMPLETE")
    logger.info("="*80)
    logger.info(f"\nOutputs saved to: {OUTPUT_DIR}")
    logger.info("\nFiles created:")
    logger.info("  - demographics_by_council_district.csv")
    logger.info("  - district_population.png")
    logger.info("  - district_income.png")
    logger.info("  - district_education.png")
    logger.info("  - district_racial_composition.png")
    logger.info("  - district_heatmap.png")
    
    return 0


if __name__ == '__main__':
    exit(main())


