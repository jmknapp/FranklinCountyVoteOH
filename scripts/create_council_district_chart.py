#!/usr/bin/env python3
"""
Create a bar chart showing demographics and Vogel support by Council District.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'processed' / 'district_analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("Loading data...")
    
    # Load demographics by council district (already computed)
    demo_path = PROJECT_ROOT / 'data' / 'processed' / 'district_analysis' / 'demographics_by_council_district.csv'
    if not demo_path.exists():
        print(f"Error: {demo_path} not found")
        print("Please run scripts/analyze_demographics_by_district.py first")
        return 1
    
    districts = pd.read_csv(demo_path)
    
    # Load precinct demographics
    precinct_demo = pd.read_csv(PROJECT_ROOT / 'data' / 'processed' / 'demographics_by_precinct_2025.csv')
    precinct_demo['PRECINCT'] = precinct_demo['PRECINCT'].str.strip().str.upper()
    
    # Load CD7 voting data
    cd7 = pd.read_csv(PROJECT_ROOT / 'data' / 'raw' / 'results_2025_columbus_cd7.csv')
    cd7['PRECINCT'] = cd7['PRECINCT'].str.strip().str.upper()
    cd7['vogel_share'] = cd7['D_votes'] / (cd7['D_votes'] + cd7['R_votes'])
    
    # Load Council District shapefile
    cc_districts = gpd.read_file(PROJECT_ROOT / 'data' / 'raw' / 'otherBoundaries' / 'CMHcc' / 'Columbus_City_Council_Districts.shp')
    
    # Load precincts shapefile
    precincts = gpd.read_file(PROJECT_ROOT / 'data' / 'raw' / 'precincts_2025' / 'VotingPrecinct.shp')
    if precincts.crs is None:
        precincts.set_crs('EPSG:3735', inplace=True)
    precincts = precincts.to_crs(cc_districts.crs)
    precincts['PRECINCT'] = precincts['NAME'].str.strip().str.upper()
    
    # Merge precinct voting with demographics
    precinct_data = precinct_demo.merge(cd7[['PRECINCT', 'vogel_share', 'D_votes', 'R_votes']], 
                                        on='PRECINCT', how='inner')
    
    # Spatial join precincts to council districts
    print("Performing spatial join...")
    precincts_with_cd = gpd.sjoin(precincts[['PRECINCT', 'geometry']], 
                                   cc_districts[['DISTRICT', 'geometry']], 
                                   how='inner', predicate='intersects')
    
    # Merge with precinct data
    precinct_data = precinct_data.merge(precincts_with_cd[['PRECINCT', 'DISTRICT']], 
                                       on='PRECINCT', how='left')
    
    # Calculate Vogel support by district (weighted by votes)
    district_vogel = []
    for district_num in range(1, 10):
        district_precincts = precinct_data[precinct_data['DISTRICT'] == district_num]
        if len(district_precincts) > 0:
            total_vogel = district_precincts['D_votes'].sum()
            total_ross = district_precincts['R_votes'].sum()
            vogel_pct = total_vogel / (total_vogel + total_ross) * 100 if (total_vogel + total_ross) > 0 else 0
            district_vogel.append({'district_num': district_num, 'vogel_support': vogel_pct})
        else:
            district_vogel.append({'district_num': district_num, 'vogel_support': 0})
    
    vogel_by_district = pd.DataFrame(district_vogel)
    
    # Merge with demographics
    districts = districts.merge(vogel_by_district, on='district_num', how='left')
    
    # Sort by district number
    districts = districts.sort_values('district_num')
    
    # Rename for easier reference
    districts['population'] = districts['total_pop']
    
    print(f"\nDistrict data:")
    print(districts[['district_num', 'pct_white', 'pct_black', 'pct_hispanic', 'vogel_support']])
    
    # Create the chart
    print("\nCreating chart...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                    gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.3})
    
    # Top panel: Demographics stacked bar chart
    x = districts['district_num'].astype(str)
    width = 0.6
    
    # Create stacked bars
    p1 = ax1.bar(x, districts['pct_white'], width, label='White', color='#4a90e2', edgecolor='black', linewidth=0.5)
    p2 = ax1.bar(x, districts['pct_black'], width, bottom=districts['pct_white'], 
                 label='Black', color='#f5a623', edgecolor='black', linewidth=0.5)
    p3 = ax1.bar(x, districts['pct_hispanic'], width, 
                 bottom=districts['pct_white'] + districts['pct_black'],
                 label='Hispanic', color='#7ed321', edgecolor='black', linewidth=0.5)
    
    ax1.set_ylabel('Percentage of Population', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Council District', fontsize=12, fontweight='bold')
    ax1.set_title('Columbus City Council Districts: Demographics and Vogel Support (2025)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='upper left', fontsize=11, framealpha=0.9)
    ax1.set_ylim(0, 100)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add percentage labels on bars
    for i, (idx, row) in enumerate(districts.iterrows()):
        # White
        if row['pct_white'] > 8:
            ax1.text(i, row['pct_white']/2, f"{row['pct_white']:.0f}%", 
                    ha='center', va='center', fontweight='bold', fontsize=9)
        # Black
        if row['pct_black'] > 8:
            ax1.text(i, row['pct_white'] + row['pct_black']/2, f"{row['pct_black']:.0f}%", 
                    ha='center', va='center', fontweight='bold', fontsize=9)
        # Hispanic
        if row['pct_hispanic'] > 3:
            ax1.text(i, row['pct_white'] + row['pct_black'] + row['pct_hispanic']/2, 
                    f"{row['pct_hispanic']:.0f}%", 
                    ha='center', va='center', fontweight='bold', fontsize=8)
    
    # Bottom panel: Vogel support
    bars = ax2.bar(x, districts['vogel_support'], width, 
                   color=['#9b59b6' if v < 50 else '#e67e22' for v in districts['vogel_support']],
                   edgecolor='black', linewidth=0.5, alpha=0.8)
    
    # Add 50% reference line
    ax2.axhline(50, color='red', linestyle='--', linewidth=2, alpha=0.7, label='50% (Even Split)')
    
    ax2.set_ylabel('Vogel Support (%)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Council District', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.grid(axis='y', alpha=0.3)
    ax2.legend(loc='upper right', fontsize=10)
    
    # Add percentage labels on bars
    for i, (bar, pct) in enumerate(zip(bars, districts['vogel_support'])):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Color legend for Vogel support
    ax2.text(0.02, 0.95, '■ Purple = Ross majority  ■ Orange = Vogel majority', 
            transform=ax2.transAxes, fontsize=9, va='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'))
    
    plt.tight_layout()
    
    # Save
    output_path = OUTPUT_DIR / 'council_districts_demographics_and_vogel.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nChart saved to: {output_path}")
    
    # Also create a summary table
    summary = districts[['district_num', 'population', 'pct_white', 'pct_black', 'pct_hispanic', 'vogel_support']].copy()
    summary['winner'] = summary['vogel_support'].apply(lambda x: 'Vogel' if x > 50 else 'Ross')
    
    print("\n" + "="*80)
    print("COUNCIL DISTRICT SUMMARY")
    print("="*80)
    for idx, row in summary.iterrows():
        print(f"\nDistrict {row['district_num']}: {row['winner']} won ({row['vogel_support']:.1f}% Vogel)")
        print(f"  Population: {row['population']:,.0f}")
        print(f"  Demographics: {row['pct_white']:.1f}% White, {row['pct_black']:.1f}% Black, {row['pct_hispanic']:.1f}% Hispanic")
    
    return 0

if __name__ == '__main__':
    exit(main())

