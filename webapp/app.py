#!/usr/bin/env python3
"""
Flask web app for comparing election results.
Allows users to select two races/issues and generates comparison maps.
"""

import os
import re
from pathlib import Path
from io import BytesIO
import base64

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration - use absolute paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
SHAPEFILE_DIR = PROJECT_ROOT / 'data' / 'raw'

# Cache for shapefiles to avoid reloading
SHAPEFILE_CACHE = {}

def get_available_races():
    """Scan data/raw directory for available race results."""
    races = []
    
    for csv_file in DATA_DIR.glob('results_*.csv'):
        filename = csv_file.stem  # Remove .csv extension
        
        # Parse filename to extract race info
        # Format: results_YEAR[_race_type][_additional_info].csv
        match = re.match(r'results_(\d{4})(?:_(.+))?', filename)
        if match:
            year = match.group(1)
            race_type = match.group(2) if match.group(2) else 'president'
            
            # Create display name
            if 'issue1' in race_type:
                display_name = f"{year} State Issue 1 (Abortion Rights)"
            elif 'issue2' in race_type:
                display_name = f"{year} State Issue 2 (Cannabis)"
            elif 'house_cd' in race_type:
                cd = race_type.split('_')[-1].upper()
                display_name = f"{year} U.S. House {cd}"
            elif race_type in ['president', 'presidential']:
                display_name = f"{year} President"
            elif race_type == 'governor':
                display_name = f"{year} Governor"
            else:
                display_name = f"{year} {race_type.replace('_', ' ').title()}"
            
            races.append({
                'id': filename,
                'year': year,
                'type': race_type,
                'display_name': display_name,
                'file_path': str(csv_file)
            })
    
    # Sort by year (descending) then by type
    races.sort(key=lambda x: (x['year'], x['type']), reverse=True)
    
    return races

def get_shapefile_for_year(year):
    """Get the appropriate shapefile for a given year."""
    year_int = int(year)
    
    # Use cached shapefile if available
    cache_key = f'shp_{year}'
    if cache_key in SHAPEFILE_CACHE:
        return SHAPEFILE_CACHE[cache_key]
    
    # Find closest available shapefile
    # Priority: same year > next year > previous year
    shapefile_dirs = sorted(SHAPEFILE_DIR.glob('precincts_*'))
    
    available_years = []
    for shp_dir in shapefile_dirs:
        match = re.match(r'precincts_(\d{4})', shp_dir.name)
        if match:
            available_years.append((int(match.group(1)), shp_dir))
    
    if not available_years:
        return None
    
    # Find closest year
    closest_year, closest_dir = min(available_years, key=lambda x: abs(x[0] - year_int))
    
    # Find shapefile in directory
    shp_files = list(closest_dir.glob('*.shp'))
    if not shp_files:
        return None
    
    # Load shapefile
    shp = gpd.read_file(shp_files[0])
    shp = shp.to_crs('EPSG:3747')
    
    # Cache it
    SHAPEFILE_CACHE[cache_key] = shp
    
    return shp

def load_race_data(race_id):
    """Load race data and merge with appropriate shapefile."""
    races = get_available_races()
    race_info = next((r for r in races if r['id'] == race_id), None)
    
    if not race_info:
        return None, None
    
    # Load results
    results = pd.read_csv(race_info['file_path'])
    results['PRECINCT'] = results['PRECINCT'].str.strip().str.upper()
    
    # Get shapefile for this year
    shp = get_shapefile_for_year(race_info['year'])
    if shp is None:
        return None, None
    
    # Find precinct ID column in shapefile
    id_col = 'NAME'
    for col in ['NAME', 'PRECINCT', 'PRECINCT_N', 'PREC_NAME']:
        if col in shp.columns:
            id_col = col
            break
    
    # Normalize IDs
    shp[id_col] = shp[id_col].astype(str).str.strip().str.upper()
    
    # Merge
    gdf = shp.merge(results, left_on=id_col, right_on='PRECINCT', how='inner')
    
    # Compute two-party share
    gdf['total'] = gdf['D_votes'] + gdf['R_votes']
    gdf['D_share'] = gdf['D_votes'] / gdf['total']
    
    return gdf, race_info

def create_comparison_map(race1_id, race2_id):
    """Create a 3-panel comparison map."""
    # Load data for both races
    gdf1, info1 = load_race_data(race1_id)
    gdf2, info2 = load_race_data(race2_id)
    
    if gdf1 is None or gdf2 is None:
        return None, "Failed to load race data"
    
    # Compute difference
    # Need to align by precinct
    id_col = 'NAME'
    for col in ['NAME', 'PRECINCT', 'PRECINCT_N', 'PREC_NAME']:
        if col in gdf1.columns:
            id_col = col
            break
    
    diff_df = gdf1[[id_col, 'D_share', 'geometry']].merge(
        gdf2[[id_col, 'D_share']],
        left_on=id_col,
        right_on=id_col,
        suffixes=('_1', '_2')
    )
    diff_df['difference'] = diff_df['D_share_1'] - diff_df['D_share_2']
    gdf_diff = gpd.GeoDataFrame(diff_df, geometry='geometry', crs=gdf1.crs)
    
    # Create figure with 3 panels
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(28, 10))
    
    # Panel 1: Race 1
    gdf1.plot(column='D_share', ax=ax1, legend=True, cmap='RdBu',
              vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
              legend_kwds={'label': 'Democratic/Yes Share', 'shrink': 0.8})
    ax1.set_title(info1['display_name'], fontsize=16, fontweight='bold')
    ax1.axis('off')
    
    # Panel 2: Race 2
    gdf2.plot(column='D_share', ax=ax2, legend=True, cmap='RdBu',
              vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
              legend_kwds={'label': 'Democratic/Yes Share', 'shrink': 0.8})
    ax2.set_title(info2['display_name'], fontsize=16, fontweight='bold')
    ax2.axis('off')
    
    # Panel 3: Difference
    vmax_diff = max(abs(gdf_diff['difference'].min()), abs(gdf_diff['difference'].max()))
    gdf_diff.plot(column='difference', ax=ax3, legend=True, cmap='RdBu',
                  vmin=-vmax_diff, vmax=vmax_diff, edgecolor='gray', linewidth=0.2,
                  legend_kwds={'label': 'Difference (Race 1 - Race 2)', 'shrink': 0.8})
    ax3.set_title(f'Difference\n(Blue = {info1["year"]} higher, Red = {info2["year"]} higher)', 
                  fontsize=16, fontweight='bold')
    ax3.axis('off')
    
    plt.tight_layout()
    
    # Save to BytesIO
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)
    
    # Encode as base64 for embedding in HTML
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Calculate statistics
    stats = {
        'race1': {
            'name': info1['display_name'],
            'pct': gdf1['D_share'].mean() * 100,
            'total_d': gdf1['D_votes'].sum(),
            'total_r': gdf1['R_votes'].sum()
        },
        'race2': {
            'name': info2['display_name'],
            'pct': gdf2['D_share'].mean() * 100,
            'total_d': gdf2['D_votes'].sum(),
            'total_r': gdf2['R_votes'].sum()
        },
        'difference': {
            'mean': diff_df['difference'].mean() * 100,
            'std': diff_df['difference'].std() * 100,
            'min': diff_df['difference'].min() * 100,
            'max': diff_df['difference'].max() * 100
        }
    }
    
    return img_base64, stats

@app.route('/')
def index():
    """Main page with race selection dropdowns."""
    races = get_available_races()
    return render_template('index.html', races=races)

@app.route('/api/races')
def api_races():
    """API endpoint to get available races."""
    races = get_available_races()
    return jsonify(races)

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """API endpoint to generate comparison map."""
    data = request.get_json()
    race1_id = data.get('race1')
    race2_id = data.get('race2')
    
    if not race1_id or not race2_id:
        return jsonify({'error': 'Both races must be selected'}), 400
    
    if race1_id == race2_id:
        return jsonify({'error': 'Please select two different races'}), 400
    
    try:
        img_base64, stats = create_comparison_map(race1_id, race2_id)
        
        if img_base64 is None:
            return jsonify({'error': stats}), 500
        
        return jsonify({
            'image': img_base64,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)

