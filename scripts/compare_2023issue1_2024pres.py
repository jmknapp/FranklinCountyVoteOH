#!/usr/bin/env python3
"""Compare 2023 State Issue 1 (Abortion Rights) to 2024 Presidential race."""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print('Creating 2023 Issue 1 (Abortion) vs 2024 Presidential comparison map...\n')

    # Load 2023 shapefile
    shp_2023 = gpd.read_file('data/raw/precincts_2023/VotingPrecinct.shp')
    shp_2023 = shp_2023.to_crs('EPSG:3747')
    print(f'Loaded {len(shp_2023)} precincts from 2023 shapefile')
    
    # Load 2025 shapefile for 2024 data
    shp_2024 = gpd.read_file('data/raw/precincts_2025/VotingPrecinct.shp')
    shp_2024 = shp_2024.to_crs('EPSG:3747')
    print(f'Loaded {len(shp_2024)} precincts from 2024/2025 shapefile')

    # Load 2023 Issue 1 results
    results_2023 = pd.read_csv('data/raw/results_2023_issue1.csv')
    results_2023['PRECINCT'] = results_2023['PRECINCT'].str.strip().str.upper()
    print(f'Loaded {len(results_2023)} precincts from 2023 Issue 1 results')

    # Load 2024 Presidential results
    results_2024 = pd.read_csv('data/raw/results_2024.csv')
    results_2024['PRECINCT'] = results_2024['PRECINCT'].str.strip().str.upper()
    print(f'Loaded {len(results_2024)} precincts from 2024 Presidential results')

    # Get precinct ID from shapefiles
    id_col_2023 = 'NAME'
    id_col_2024 = 'NAME'
    for col in ['NAME', 'PRECINCT', 'PRECINCT_N', 'PREC_NAME']:
        if col in shp_2023.columns:
            id_col_2023 = col
            break
    for col in ['NAME', 'PRECINCT', 'PRECINCT_N', 'PREC_NAME']:
        if col in shp_2024.columns:
            id_col_2024 = col
            break

    print(f'Using shapefile ID columns: 2023={id_col_2023}, 2024={id_col_2024}')

    # Normalize shapefile IDs
    shp_2023[id_col_2023] = shp_2023[id_col_2023].astype(str).str.strip().str.upper()
    shp_2024[id_col_2024] = shp_2024[id_col_2024].astype(str).str.strip().str.upper()

    # Merge with results
    gdf_2023 = shp_2023.merge(results_2023, left_on=id_col_2023, right_on='PRECINCT', how='inner')
    gdf_2024 = shp_2024.merge(results_2024, left_on=id_col_2024, right_on='PRECINCT', how='inner')

    print(f'\nMatched {len(gdf_2023)} precincts for 2023 Issue 1')
    print(f'Matched {len(gdf_2024)} precincts for 2024 Presidential')

    # Compute two-party shares (for Issue 1, Yes=D, No=R)
    gdf_2023['total'] = gdf_2023['D_votes'] + gdf_2023['R_votes']
    gdf_2023['D_share'] = gdf_2023['D_votes'] / gdf_2023['total']
    
    gdf_2024['total'] = gdf_2024['D_votes'] + gdf_2024['R_votes']
    gdf_2024['D_share'] = gdf_2024['D_votes'] / gdf_2024['total']

    # Create comparison map
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # 2023 Issue 1 (Abortion Rights)
    gdf_2023.plot(column='D_share', ax=ax1, legend=True, cmap='RdBu',
                  vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
                  legend_kwds={'label': 'Yes Share (Pro-Choice)', 'shrink': 0.8})
    ax1.set_title('2023 State Issue 1 (Abortion Rights)', fontsize=16, fontweight='bold')
    ax1.axis('off')

    # 2024 Presidential
    gdf_2024.plot(column='D_share', ax=ax2, legend=True, cmap='RdBu',
                  vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
                  legend_kwds={'label': 'Democratic Two-Party Share', 'shrink': 0.8})
    ax2.set_title('2024 President (Harris vs Trump)', fontsize=16, fontweight='bold')
    ax2.axis('off')

    plt.tight_layout()
    plt.savefig('data/processed/maps/2023_issue1_vs_2024_pres_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Calculate summary statistics
    total_yes_2023 = gdf_2023['D_votes'].sum()
    total_votes_2023 = gdf_2023['total'].sum()
    pct_yes_2023 = 100 * total_yes_2023 / total_votes_2023
    
    total_d_2024 = gdf_2024['D_votes'].sum()
    total_votes_2024 = gdf_2024['total'].sum()
    pct_d_2024 = 100 * total_d_2024 / total_votes_2024

    print('\n=== COMPARISON SUMMARY ===')
    print(f'2023 Issue 1 (Abortion): {pct_yes_2023:.1f}% Yes')
    print(f'2024 Presidential: {pct_d_2024:.1f}% Democratic')
    print(f'Difference: {pct_yes_2023 - pct_d_2024:.1f} percentage points')
    print('\n✓ Saved comparison map: data/processed/maps/2023_issue1_vs_2024_pres_comparison.png')

if __name__ == '__main__':
    main()

