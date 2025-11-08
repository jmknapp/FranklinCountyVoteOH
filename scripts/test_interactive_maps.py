#!/usr/bin/env python3
"""
Standalone test script to try interactive Folium maps.
Generates HTML files you can open in a browser.
No changes to the web app - just a test!
"""

import sys
sys.path.insert(0, 'src')

import geopandas as gpd
import pandas as pd
import folium
from folium import plugins
import branca.colormap as cm

def normalize_precinct_name(name):
    """Normalize precinct names for matching across years."""
    name = str(name).strip().upper()
    replacements = {
        'COLS ': 'COLUMBUS ',
        'REYN ': 'REYNOLDSBURG ',
        'UPPER ARL ': 'UPPER ARLINGTON ',
        'WORTH ': 'WORTHINGTON ',
    }
    for abbrev, full in replacements.items():
        if name.startswith(abbrev):
            name = name.replace(abbrev, full, 1)
            break
    return name

def load_race(race_file, shapefile_path):
    """Load race data and merge with shapefile."""
    # Load shapefile
    shp = gpd.read_file(shapefile_path)
    shp = shp.to_crs('EPSG:4326')  # WGS84 for Folium
    
    # Load results
    results = pd.read_csv(race_file)
    results['PRECINCT'] = results['PRECINCT'].str.strip().str.upper()
    
    # Find ID column
    id_col = 'NAME'
    for col in ['NAME', 'PRECINCT', 'PRECINCT_N', 'PREC_NAME']:
        if col in shp.columns:
            id_col = col
            break
    
    # Normalize
    shp[id_col] = shp[id_col].astype(str).str.strip().str.upper()
    
    # Merge
    gdf = shp.merge(results, left_on=id_col, right_on='PRECINCT', how='inner')
    
    # Compute share
    gdf['total'] = gdf['D_votes'] + gdf['R_votes']
    gdf['D_share'] = gdf['D_votes'] / gdf['total']
    
    # Convert any Timestamp columns to strings for JSON serialization
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)
    
    return gdf

def create_folium_choropleth(gdf, column, title, colormap_name='RdBu', vmin=0, vmax=1):
    """Create an interactive Folium choropleth map."""
    # Get center coordinates
    bounds = gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'  # Clean, light basemap
    )
    
    # Create colormap
    if colormap_name == 'RdBu':
        colormap = cm.LinearColormap(
            colors=['#b2182b', '#ef8a62', '#fddbc7', '#f7f7f7', '#d1e5f0', '#67a9cf', '#2166ac'],
            vmin=vmin,
            vmax=vmax,
            caption=title
        )
    else:  # PRGn for difference
        colormap = cm.LinearColormap(
            colors=['#762a83', '#af8dc3', '#e7d4e8', '#f7f7f7', '#d9f0d3', '#7fbf7b', '#1b7837'],
            vmin=vmin,
            vmax=vmax,
            caption=title
        )
    
    # Add choropleth
    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties'][column]) if feature['properties'][column] is not None else 'gray',
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['PRECINCT', column, 'D_votes', 'R_votes', 'total'],
            aliases=['Precinct:', f'{column.replace("_", " ").title()}:', 'Dem/Prog Votes:', 'Rep/Cons Votes:', 'Total Votes:'],
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: white;
                border: 2px solid black;
                border-radius: 3px;
                box-shadow: 3px;
            """,
            max_width=300,
        )
    ).add_to(m)
    
    # Add colormap to map
    colormap.add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 50px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:18px; font-weight: bold; padding: 10px">
        {title}
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    return m

def main():
    print('🗺️  Interactive Map Test - Folium Comparison\n')
    print('This script generates 3 interactive HTML maps:')
    print('  1. Race 1 (2023 Issue 1 - Abortion Rights)')
    print('  2. Race 2 (2024 President)')
    print('  3. Difference map\n')
    
    # Load data
    print('Loading data...')
    race1_file = 'data/raw/results_2023_issue1.csv'
    race2_file = 'data/raw/results_2024.csv'
    shp1_path = 'data/raw/precincts_2023/VotingPrecinct.shp'
    shp2_path = 'data/raw/precincts_2025/VotingPrecinct.shp'
    
    gdf1 = load_race(race1_file, shp1_path)
    gdf2 = load_race(race2_file, shp2_path)
    
    print(f'  Race 1: {len(gdf1)} precincts matched')
    print(f'  Race 2: {len(gdf2)} precincts matched')
    
    # Create difference data
    print('\nComputing difference...')
    id_col = 'NAME'
    gdf1['precinct_normalized'] = gdf1[id_col].apply(normalize_precinct_name)
    gdf2['precinct_normalized'] = gdf2[id_col].apply(normalize_precinct_name)
    
    diff_df = gdf1[[id_col, 'precinct_normalized', 'D_share', 'geometry', 'PRECINCT', 'D_votes', 'R_votes', 'total']].merge(
        gdf2[['precinct_normalized', 'D_share']],
        on='precinct_normalized',
        suffixes=('_1', '_2')
    )
    diff_df['difference'] = diff_df['D_share_1'] - diff_df['D_share_2']
    gdf_diff = gpd.GeoDataFrame(diff_df, geometry='geometry', crs=gdf1.crs)
    
    print(f'  {len(gdf_diff)} precincts in difference map')
    
    # Create maps
    print('\nGenerating interactive maps...')
    
    print('  1/3 Creating map for 2023 Issue 1...')
    m1 = create_folium_choropleth(
        gdf1, 
        'D_share',
        '2023 Issue 1 (Abortion Rights) - Yes Share',
        colormap_name='RdBu'
    )
    m1.save('test_map_2023_issue1.html')
    
    print('  2/3 Creating map for 2024 President...')
    m2 = create_folium_choropleth(
        gdf2,
        'D_share',
        '2024 President (Harris vs Trump) - Democratic Share',
        colormap_name='RdBu'
    )
    m2.save('test_map_2024_president.html')
    
    print('  3/3 Creating difference map...')
    vmax_diff = max(abs(gdf_diff['difference'].min()), abs(gdf_diff['difference'].max()))
    m3 = create_folium_choropleth(
        gdf_diff,
        'difference',
        'Difference: Issue 1 - Presidential (Green=Issue1 higher, Purple=President higher)',
        colormap_name='PRGn',
        vmin=-vmax_diff,
        vmax=vmax_diff
    )
    m3.save('test_map_difference.html')
    
    print('\n✅ Done! Interactive maps created:\n')
    print('  📄 test_map_2023_issue1.html')
    print('  📄 test_map_2024_president.html')
    print('  📄 test_map_difference.html')
    print('\n🌐 Open these files in your web browser to test!')
    print('\n📋 Features to try:')
    print('  • Zoom in/out with mouse wheel')
    print('  • Click and drag to pan')
    print('  • Hover over precincts to see vote details')
    print('  • Click fullscreen button (top left)')
    print('  • Notice automatic street basemap')
    print('\n💡 If you like it, we can integrate into the web app!')

if __name__ == '__main__':
    main()

