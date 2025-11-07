#!/usr/bin/env python3
"""Compare 2018 Governor race to 2024 Presidential race."""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print('Creating 2018 Governor vs 2024 Presidential comparison map...\n')

    # Load 2017 shapefile for 2018 data (closest available)
    shp_2018 = gpd.read_file('data/raw/precincts_2017/VotingPrecinct.shp')
    shp_2018 = shp_2018.to_crs('EPSG:3747')
    print(f'Loaded {len(shp_2018)} precincts from 2017/2018 shapefile')
    
    # Load 2025 shapefile for 2024 data
    shp_2024 = gpd.read_file('data/raw/precincts_2025/VotingPrecinct.shp')
    shp_2024 = shp_2024.to_crs('EPSG:3747')
    print(f'Loaded {len(shp_2024)} precincts from 2024/2025 shapefile')

    # Load 2018 Governor results
    results_2018 = pd.read_csv('data/raw/results_2018.csv')
    results_2018['PRECINCT'] = results_2018['PRECINCT'].str.strip().str.upper()
    print(f'Loaded {len(results_2018)} precincts from 2018 Governor results')

    # Load 2024 Presidential results
    results_2024 = pd.read_csv('data/raw/results_2024.csv')
    results_2024['PRECINCT'] = results_2024['PRECINCT'].str.strip().str.upper()
    print(f'Loaded {len(results_2024)} precincts from 2024 Presidential results')

    # Get precinct ID from shapefiles (they use different column names)
    id_col_2018 = 'NAME'
    id_col_2024 = 'PRECINCT'
    for col in ['PRECINCT', 'NAME', 'PRECINCT_N', 'PREC_NAME']:
        if col in shp_2024.columns:
            id_col_2024 = col
            break

    print(f'Using shapefile ID columns: 2018={id_col_2018}, 2024={id_col_2024}')

    # Normalize shapefile IDs
    shp_2018[id_col_2018] = shp_2018[id_col_2018].astype(str).str.strip().str.upper()
    shp_2024[id_col_2024] = shp_2024[id_col_2024].astype(str).str.strip().str.upper()

    # Merge with results
    gdf_2018 = shp_2018.merge(results_2018, left_on=id_col_2018, right_on='PRECINCT', how='inner')
    gdf_2024 = shp_2024.merge(results_2024, left_on=id_col_2024, right_on='PRECINCT', how='inner')

    print(f'\nMatched {len(gdf_2018)} precincts for 2018')
    print(f'Matched {len(gdf_2024)} precincts for 2024')

    # Compute two-party shares
    gdf_2018['total'] = gdf_2018['D_votes'] + gdf_2018['R_votes']
    gdf_2018['D_share'] = gdf_2018['D_votes'] / gdf_2018['total']
    
    gdf_2024['total'] = gdf_2024['D_votes'] + gdf_2024['R_votes']
    gdf_2024['D_share'] = gdf_2024['D_votes'] / gdf_2024['total']

    # Create comparison map
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # 2018 Governor
    gdf_2018.plot(column='D_share', ax=ax1, legend=True, cmap='RdBu',
                  vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
                  legend_kwds={'label': 'Democratic Two-Party Share', 'shrink': 0.8})
    ax1.set_title('2018 Governor (Cordray vs DeWine)', fontsize=16, fontweight='bold')
    ax1.axis('off')

    # 2024 Presidential
    gdf_2024.plot(column='D_share', ax=ax2, legend=True, cmap='RdBu',
                  vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
                  legend_kwds={'label': 'Democratic Two-Party Share', 'shrink': 0.8})
    ax2.set_title('2024 President (Harris vs Trump)', fontsize=16, fontweight='bold')
    ax2.axis('off')

    plt.tight_layout()
    plt.savefig('data/processed/maps/2018_gov_vs_2024_pres_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    print('\n✓ Saved comparison map: data/processed/maps/2018_gov_vs_2024_pres_comparison.png')

if __name__ == '__main__':
    main()

