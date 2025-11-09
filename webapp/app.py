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

import folium
import folium.plugins as plugins
from branca import colormap as cm
import geopandas as gpd
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration - use absolute paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
SHAPEFILE_DIR = PROJECT_ROOT / 'data' / 'raw'
METADATA_FILE = Path(__file__).parent / 'race_metadata.yaml'

# Cache for shapefiles to avoid reloading
SHAPEFILE_CACHE = {}

# Load race metadata
RACE_METADATA = {}
if METADATA_FILE.exists():
    with open(METADATA_FILE, 'r') as f:
        metadata_config = yaml.safe_load(f)
        RACE_METADATA = metadata_config.get('races', {})

def normalize_precinct_name(name):
    """
    Normalize precinct names to a standard format for cross-year comparisons.
    Converts abbreviations to full names to ensure consistency.
    """
    name = str(name).strip().upper()
    
    # Standardize common abbreviations to full names
    replacements = {
        'COLS ': 'COLUMBUS ',
        'REYN ': 'REYNOLDSBURG ',
        'UPPER ARL ': 'UPPER ARLINGTON ',
        'WORTH ': 'WORTHINGTON ',
        'CANAL WIN ': 'CANAL WINCHESTER ',
        'GAHANNA ': 'GAHANNA ',
        'GAH ': 'GAHANNA ',
        'HILLIARD ': 'HILLIARD ',
        'HIL ': 'HILLIARD ',
        'WESTERVILLE ': 'WESTERVILLE ',
        'WEST ': 'WESTERVILLE ',
    }
    
    for abbrev, full in replacements.items():
        if name.startswith(abbrev):
            name = name.replace(abbrev, full, 1)
            break
    
    return name

def get_available_races():
    """Scan data/raw directory for available race results."""
    races = []
    
    for csv_file in DATA_DIR.glob('results_*.csv'):
        filename = csv_file.stem  # Remove .csv extension
        
        # Check if we have metadata for this race
        if filename in RACE_METADATA:
            metadata = RACE_METADATA[filename]
            races.append({
                'id': filename,
                'year': str(metadata.get('year', '')),
                'type': metadata.get('race_type', ''),
                'display_name': metadata.get('display_name', filename),
                'candidates': metadata.get('candidates', ''),
                'description': metadata.get('description', ''),
                'file_path': str(csv_file)
            })
        else:
            # Fallback: parse filename if no metadata
            match = re.match(r'results_(\d{4})(?:_(.+))?', filename)
            if match:
                year = match.group(1)
                race_type = match.group(2) if match.group(2) else 'president'
                
                # Create display name
                if 'issue1' in race_type:
                    display_name = f"{year} State Issue 1"
                elif 'issue2' in race_type:
                    display_name = f"{year} State Issue 2"
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
                    'candidates': '',
                    'description': '',
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
    # Try multiple common naming patterns
    possible_names = [
        'VotingPrecinct.shp',
        'Voting_Precinct.shp',
        'Voting-Precincts-G*.shp',
        'Precincts*.shp'
    ]
    
    shp_file = None
    for pattern in possible_names:
        if '*' in pattern:
            matches = list(closest_dir.glob(pattern))
            if matches:
                shp_file = matches[0]
                break
        else:
            candidate = closest_dir / pattern
            if candidate.exists():
                shp_file = candidate
                break
    
    if not shp_file:
        # Fallback: just get any .shp file
        shp_files = list(closest_dir.glob('*.shp'))
        if not shp_files:
            return None
        shp_file = shp_files[0]
    
    # Load shapefile - try/except in case file is corrupted
    try:
        shp = gpd.read_file(shp_file)
        # If no CRS defined, assume Ohio State Plane South (common for Franklin County)
        if shp.crs is None:
            shp = shp.set_crs('EPSG:3747')
        elif shp.crs != 'EPSG:3747':
            shp = shp.to_crs('EPSG:3747')
    except Exception as e:
        # Try other .shp files in the directory
        for alt_shp in closest_dir.glob('*.shp'):
            if alt_shp != shp_file:
                try:
                    shp = gpd.read_file(alt_shp)
                    if shp.crs is None:
                        shp = shp.set_crs('EPSG:3747')
                    elif shp.crs != 'EPSG:3747':
                        shp = shp.to_crs('EPSG:3747')
                    break
                except:
                    continue
        else:
            return None
    
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

def create_comparison_map_static(race1_id, race2_id):
    """Create a 3-panel comparison map as static PNG."""
    # Load data for both races
    gdf1, info1 = load_race_data(race1_id)
    gdf2, info2 = load_race_data(race2_id)
    
    if gdf1 is None or gdf2 is None:
        return None, "Failed to load race data"
    
    # Compute difference
    # Need to align by precinct using normalized names for cross-year comparison
    id_col = 'NAME'
    for col in ['NAME', 'PRECINCT', 'PRECINCT_N', 'PREC_NAME']:
        if col in gdf1.columns:
            id_col = col
            break
    
    # Create normalized precinct columns for matching
    gdf1['precinct_normalized'] = gdf1[id_col].apply(normalize_precinct_name)
    gdf2['precinct_normalized'] = gdf2[id_col].apply(normalize_precinct_name)
    
    diff_df = gdf1[[id_col, 'precinct_normalized', 'D_share', 'geometry']].merge(
        gdf2[['precinct_normalized', 'D_share']],
        on='precinct_normalized',
        suffixes=('_1', '_2')
    )
    diff_df['difference'] = diff_df['D_share_1'] - diff_df['D_share_2']
    gdf_diff = gpd.GeoDataFrame(diff_df, geometry='geometry', crs=gdf1.crs)
    
    # Create figure with 3 panels
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(28, 10))
    
    # Panel 1: Race 1
    gdf1.plot(column='D_share', ax=ax1, legend=True, cmap='RdBu',
              vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
              legend_kwds={'label': 'Democratic/Progressive Share', 'shrink': 0.8})
    ax1.set_title(info1['display_name'], fontsize=16, fontweight='bold')
    ax1.axis('off')
    
    # Panel 2: Race 2
    gdf2.plot(column='D_share', ax=ax2, legend=True, cmap='RdBu',
              vmin=0, vmax=1, edgecolor='gray', linewidth=0.2,
              legend_kwds={'label': 'Democratic/Progressive Share', 'shrink': 0.8})
    ax2.set_title(info2['display_name'], fontsize=16, fontweight='bold')
    ax2.axis('off')
    
    # Panel 3: Difference (using purple-green to avoid R/D confusion)
    vmax_diff = max(abs(gdf_diff['difference'].min()), abs(gdf_diff['difference'].max()))
    gdf_diff.plot(column='difference', ax=ax3, legend=True, cmap='PRGn',
                  vmin=-vmax_diff, vmax=vmax_diff, edgecolor='gray', linewidth=0.2,
                  legend_kwds={'label': 'Difference (Race 1 - Race 2)', 'shrink': 0.8})
    ax3.set_title(f'Difference\n(Green = {info1["display_name"]} higher\nPurple = {info2["display_name"]} higher)', 
                  fontsize=14, fontweight='bold')
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
            'pct': float(gdf1['D_share'].mean() * 100),
            'total_d': int(gdf1['D_votes'].sum()),
            'total_r': int(gdf1['R_votes'].sum())
        },
        'race2': {
            'name': info2['display_name'],
            'pct': float(gdf2['D_share'].mean() * 100),
            'total_d': int(gdf2['D_votes'].sum()),
            'total_r': int(gdf2['R_votes'].sum())
        },
        'difference': {
            'mean': float(diff_df['difference'].mean() * 100),
            'std': float(diff_df['difference'].std() * 100),
            'min': float(diff_df['difference'].min() * 100),
            'max': float(diff_df['difference'].max() * 100)
        }
    }
    
    return img_base64, stats

def create_comparison_map_folium(race1_id, race2_id):
    """Create a 3-panel comparison with interactive Folium maps."""
    import folium
    from folium import plugins
    import branca.colormap as cm
    
    # Load data for both races
    gdf1, info1 = load_race_data(race1_id)
    gdf2, info2 = load_race_data(race2_id)
    
    if gdf1 is None or gdf2 is None:
        return None, "Failed to load race data"
    
    # Convert to WGS84 for Folium
    gdf1 = gdf1.to_crs('EPSG:4326')
    gdf2 = gdf2.to_crs('EPSG:4326')
    
    # Convert any Timestamp columns to strings
    for gdf in [gdf1, gdf2]:
        for col in gdf.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].astype(str)
    
    # Compute difference
    id_col = 'NAME'
    for col in ['NAME', 'PRECINCT', 'PRECINCT_N', 'PREC_NAME']:
        if col in gdf1.columns:
            id_col = col
            break
    
    gdf1['precinct_normalized'] = gdf1[id_col].apply(normalize_precinct_name)
    gdf2['precinct_normalized'] = gdf2[id_col].apply(normalize_precinct_name)
    
    diff_df = gdf1[[id_col, 'precinct_normalized', 'D_share', 'geometry', 'PRECINCT', 'D_votes', 'R_votes', 'total']].merge(
        gdf2[['precinct_normalized', 'D_share']],
        on='precinct_normalized',
        suffixes=('_1', '_2')
    )
    diff_df['difference'] = diff_df['D_share_1'] - diff_df['D_share_2']
    gdf_diff = gpd.GeoDataFrame(diff_df, geometry='geometry', crs=gdf1.crs)
    
    # Get center for maps
    bounds = gdf1.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create three Folium maps
    maps_html = []
    
    # Map 1: Race 1
    m1 = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='CartoDB positron')
    colormap1 = cm.LinearColormap(
        colors=['#b2182b', '#ef8a62', '#fddbc7', '#f7f7f7', '#d1e5f0', '#67a9cf', '#2166ac'],
        vmin=0, vmax=1, caption='Democratic/Progressive Share'
    )
    folium.GeoJson(
        gdf1,
        style_function=lambda feature: {
            'fillColor': colormap1(feature['properties']['D_share']) if feature['properties']['D_share'] is not None else 'gray',
            'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['PRECINCT', 'D_share', 'D_votes', 'R_votes', 'total'],
            aliases=['Precinct:', 'Dem/Prog Share:', 'Dem/Prog Votes:', 'Rep/Cons Votes:', 'Total:'],
            localize=True, sticky=False, labels=True,
            style="background-color: white; border: 2px solid black; border-radius: 3px; box-shadow: 3px;",
            max_width=300,
        )
    ).add_to(m1)
    colormap1.add_to(m1)
    plugins.Fullscreen().add_to(m1)
    
    # Add title as a Leaflet control (stays with map in fullscreen)
    title_control1 = f'''
    <script>
        window.addEventListener('load', function() {{
            var map = null;
            for (var key in window) {{
                if (window[key] instanceof L.Map) {{
                    map = window[key];
                    break;
                }}
            }}
            if (map) {{
                var titleDiv = null;
                L.Control.Title = L.Control.extend({{
                    onAdd: function(map) {{
                        titleDiv = L.DomUtil.create('div', 'leaflet-control-title-dynamic');
                        titleDiv.innerHTML = '{info1['display_name']}';
                        titleDiv.style.backgroundColor = 'white';
                        titleDiv.style.border = '2px solid grey';
                        titleDiv.style.borderRadius = '4px';
                        titleDiv.style.padding = '10px';
                        titleDiv.style.fontSize = '18px';
                        titleDiv.style.fontWeight = 'bold';
                        titleDiv.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
                        titleDiv.style.maxWidth = '500px';
                        titleDiv.style.display = 'none';  // Hidden by default
                        return titleDiv;
                    }}
                }});
                var titleControl = new L.Control.Title({{ position: 'topleft' }});
                titleControl.addTo(map);
                
                // Listen for fullscreen changes on the document
                function updateTitleVisibility() {{
                    if (titleDiv) {{
                        // Check if we're in fullscreen mode
                        var isFullscreen = document.fullscreenElement || 
                                         document.webkitFullscreenElement || 
                                         document.mozFullScreenElement ||
                                         document.msFullscreenElement;
                        titleDiv.style.display = isFullscreen ? 'block' : 'none';
                    }}
                }}
                
                // Listen to multiple fullscreen events
                document.addEventListener('fullscreenchange', updateTitleVisibility);
                document.addEventListener('webkitfullscreenchange', updateTitleVisibility);
                document.addEventListener('mozfullscreenchange', updateTitleVisibility);
                document.addEventListener('MSFullscreenChange', updateTitleVisibility);
                
                // Also listen to Leaflet's own event if available
                if (map.on) {{
                    map.on('fullscreenchange', updateTitleVisibility);
                }}
            }}
        }});
    </script>
    '''
    m1.get_root().html.add_child(folium.Element(title_control1))
    
    # Force map to fill the entire iframe
    fill_css = '''<style>
        html, body {
            width: 100% !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .folium-map, #map, div.folium-map {
            width: 100% !important;
            height: 100% !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
        }
        /* Move color legend to bottom center */
        .leaflet-top.leaflet-right {
            top: auto !important;
            bottom: 10px !important;
            left: 50% !important;
            right: auto !important;
            transform: translateX(-50%) !important;
        }
    </style>'''
    m1.get_root().html.add_child(folium.Element(fill_css))
    
    # Add Home button to reset view
    home_button = f'''
    <script>
        window.addEventListener('load', function() {{
            var map = null;
            for (var key in window) {{
                if (window[key] instanceof L.Map) {{
                    map = window[key];
                    break;
                }}
            }}
            if (map) {{
                L.Control.HomeButton = L.Control.extend({{
                    onAdd: function(map) {{
                        var button = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                        button.innerHTML = '🏠';
                        button.style.backgroundColor = 'white';
                        button.style.width = '34px';
                        button.style.height = '34px';
                        button.style.lineHeight = '34px';
                        button.style.textAlign = 'center';
                        button.style.cursor = 'pointer';
                        button.style.fontSize = '18px';
                        button.title = 'Reset to initial view';
                        button.onclick = function() {{
                            map.setView([{center_lat}, {center_lon}], 10);
                        }};
                        return button;
                    }}
                }});
                var homeControl = new L.Control.HomeButton({{ position: 'topleft' }});
                homeControl.addTo(map);
            }}
        }});
    </script>
    '''
    m1.get_root().html.add_child(folium.Element(home_button))
    
    # Map 2: Race 2  
    m2 = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='CartoDB positron')
    colormap2 = cm.LinearColormap(
        colors=['#b2182b', '#ef8a62', '#fddbc7', '#f7f7f7', '#d1e5f0', '#67a9cf', '#2166ac'],
        vmin=0, vmax=1, caption='Democratic/Progressive Share'
    )
    folium.GeoJson(
        gdf2,
        style_function=lambda feature: {
            'fillColor': colormap2(feature['properties']['D_share']) if feature['properties']['D_share'] is not None else 'gray',
            'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['PRECINCT', 'D_share', 'D_votes', 'R_votes', 'total'],
            aliases=['Precinct:', 'Dem/Prog Share:', 'Dem/Prog Votes:', 'Rep/Cons Votes:', 'Total:'],
            localize=True, sticky=False, labels=True,
            style="background-color: white; border: 2px solid black; border-radius: 3px; box-shadow: 3px;",
            max_width=300,
        )
    ).add_to(m2)
    colormap2.add_to(m2)
    plugins.Fullscreen().add_to(m2)
    
    # Add title as a Leaflet control (stays with map in fullscreen)
    title_control2 = f'''
    <script>
        window.addEventListener('load', function() {{
            var map = null;
            for (var key in window) {{
                if (window[key] instanceof L.Map) {{
                    map = window[key];
                    break;
                }}
            }}
            if (map) {{
                var titleDiv = null;
                L.Control.Title = L.Control.extend({{
                    onAdd: function(map) {{
                        titleDiv = L.DomUtil.create('div', 'leaflet-control-title-dynamic');
                        titleDiv.innerHTML = '{info2['display_name']}';
                        titleDiv.style.backgroundColor = 'white';
                        titleDiv.style.border = '2px solid grey';
                        titleDiv.style.borderRadius = '4px';
                        titleDiv.style.padding = '10px';
                        titleDiv.style.fontSize = '18px';
                        titleDiv.style.fontWeight = 'bold';
                        titleDiv.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
                        titleDiv.style.maxWidth = '500px';
                        titleDiv.style.display = 'none';  // Hidden by default
                        return titleDiv;
                    }}
                }});
                var titleControl = new L.Control.Title({{ position: 'topleft' }});
                titleControl.addTo(map);
                
                // Listen for fullscreen changes on the document
                function updateTitleVisibility() {{
                    if (titleDiv) {{
                        // Check if we're in fullscreen mode
                        var isFullscreen = document.fullscreenElement || 
                                         document.webkitFullscreenElement || 
                                         document.mozFullScreenElement ||
                                         document.msFullscreenElement;
                        titleDiv.style.display = isFullscreen ? 'block' : 'none';
                    }}
                }}
                
                // Listen to multiple fullscreen events
                document.addEventListener('fullscreenchange', updateTitleVisibility);
                document.addEventListener('webkitfullscreenchange', updateTitleVisibility);
                document.addEventListener('mozfullscreenchange', updateTitleVisibility);
                document.addEventListener('MSFullscreenChange', updateTitleVisibility);
                
                // Also listen to Leaflet's own event if available
                if (map.on) {{
                    map.on('fullscreenchange', updateTitleVisibility);
                }}
            }}
        }});
    </script>
    '''
    m2.get_root().html.add_child(folium.Element(title_control2))
    
    m2.get_root().html.add_child(folium.Element(fill_css))
    m2.get_root().html.add_child(folium.Element(home_button))
    
    # Map 3: Difference
    m3 = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='CartoDB positron')
    vmax_diff = max(abs(gdf_diff['difference'].min()), abs(gdf_diff['difference'].max()))
    colormap3 = cm.LinearColormap(
        colors=['#762a83', '#af8dc3', '#e7d4e8', '#f7f7f7', '#d9f0d3', '#7fbf7b', '#1b7837'],
        vmin=-vmax_diff, vmax=vmax_diff, caption='Difference'
    )
    folium.GeoJson(
        gdf_diff,
        style_function=lambda feature: {
            'fillColor': colormap3(feature['properties']['difference']) if feature['properties']['difference'] is not None else 'gray',
            'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['PRECINCT', 'difference', 'D_share_1', 'D_share_2'],
            aliases=['Precinct:', 'Difference:', 'Race 1 Share:', 'Race 2 Share:'],
            localize=True, sticky=False, labels=True,
            style="background-color: white; border: 2px solid black; border-radius: 3px; box-shadow: 3px;",
            max_width=300,
        )
    ).add_to(m3)
    colormap3.add_to(m3)
    plugins.Fullscreen().add_to(m3)
    
    # Add title as a Leaflet control (stays with map in fullscreen)
    title_text3 = f"Difference (Green = {info1['display_name']} higher, Purple = {info2['display_name']} higher)"
    title_control3 = f'''
    <script>
        window.addEventListener('load', function() {{
            var map = null;
            for (var key in window) {{
                if (window[key] instanceof L.Map) {{
                    map = window[key];
                    break;
                }}
            }}
            if (map) {{
                var titleDiv = null;
                L.Control.Title = L.Control.extend({{
                    onAdd: function(map) {{
                        titleDiv = L.DomUtil.create('div', 'leaflet-control-title-dynamic');
                        titleDiv.innerHTML = '{title_text3}';
                        titleDiv.style.backgroundColor = 'white';
                        titleDiv.style.border = '2px solid grey';
                        titleDiv.style.borderRadius = '4px';
                        titleDiv.style.padding = '10px';
                        titleDiv.style.fontSize = '16px';
                        titleDiv.style.fontWeight = 'bold';
                        titleDiv.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
                        titleDiv.style.maxWidth = '600px';
                        titleDiv.style.display = 'none';  // Hidden by default
                        return titleDiv;
                    }}
                }});
                var titleControl = new L.Control.Title({{ position: 'topleft' }});
                titleControl.addTo(map);
                
                // Listen for fullscreen changes on the document
                function updateTitleVisibility() {{
                    if (titleDiv) {{
                        // Check if we're in fullscreen mode
                        var isFullscreen = document.fullscreenElement || 
                                         document.webkitFullscreenElement || 
                                         document.mozFullScreenElement ||
                                         document.msFullscreenElement;
                        titleDiv.style.display = isFullscreen ? 'block' : 'none';
                    }}
                }}
                
                // Listen to multiple fullscreen events
                document.addEventListener('fullscreenchange', updateTitleVisibility);
                document.addEventListener('webkitfullscreenchange', updateTitleVisibility);
                document.addEventListener('mozfullscreenchange', updateTitleVisibility);
                document.addEventListener('MSFullscreenChange', updateTitleVisibility);
                
                // Also listen to Leaflet's own event if available
                if (map.on) {{
                    map.on('fullscreenchange', updateTitleVisibility);
                }}
            }}
        }});
    </script>
    '''
    m3.get_root().html.add_child(folium.Element(title_control3))
    
    m3.get_root().html.add_child(folium.Element(fill_css))
    m3.get_root().html.add_child(folium.Element(home_button))
    
    # Get the HTML for each map and wrap with unique IDs
    map1_html = m1._repr_html_().replace('<div', '<div id="map1"', 1)
    map2_html = m2._repr_html_().replace('<div', '<div id="map2"', 1)
    map3_html = m3._repr_html_().replace('<div', '<div id="map3"', 1)
    
    maps_html = [map1_html, map2_html, map3_html]
    
    # Calculate statistics (same as static version)
    stats = {
        'race1': {
            'name': info1['display_name'],
            'pct': float(gdf1['D_share'].mean() * 100),
            'total_d': int(gdf1['D_votes'].sum()),
            'total_r': int(gdf1['R_votes'].sum())
        },
        'race2': {
            'name': info2['display_name'],
            'pct': float(gdf2['D_share'].mean() * 100),
            'total_d': int(gdf2['D_votes'].sum()),
            'total_r': int(gdf2['R_votes'].sum())
        },
        'difference': {
            'mean': float(diff_df['difference'].mean() * 100),
            'std': float(diff_df['difference'].std() * 100),
            'min': float(diff_df['difference'].min() * 100),
            'max': float(diff_df['difference'].max() * 100)
        }
    }
    
    return maps_html, stats

@app.route('/')
def index():
    """Main page with race selection dropdowns."""
    races = get_available_races()
    return render_template('index.html', races=races)


@app.route('/onemap')
def onemap():
    """Single map viewer with color scheme selector."""
    races = get_available_races()
    return render_template('onemap.html', races=races)

@app.route('/test')
def test_interactive():
    """Link to test interactive maps."""
    return '''
    <html>
    <head>
        <title>Interactive Map Tests</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #667eea; }
            .map-link { display: block; padding: 15px; margin: 10px 0; background: #f0f0f0; 
                        border-radius: 8px; text-decoration: none; color: #333; border-left: 4px solid #667eea; }
            .map-link:hover { background: #e0e0e0; }
            .back { margin-top: 30px; }
        </style>
    </head>
    <body>
        <h1>🗺️ Interactive Map Tests</h1>
        <p>These are test versions of the comparison maps using Folium for interactivity.</p>
        <p><strong>Features:</strong> Zoom with mouse wheel, pan by dragging, hover for details</p>
        
        <a class="map-link" href="/test/issue1">
            <strong>Test Map 1:</strong> 2023 Issue 1 (Abortion Rights)<br>
            <small>Interactive choropleth with tooltips and street basemap</small>
        </a>
        
        <a class="map-link" href="/test/president">
            <strong>Test Map 2:</strong> 2024 President (Harris vs Trump)<br>
            <small>Interactive choropleth with tooltips and street basemap</small>
        </a>
        
        <a class="map-link" href="/test/difference">
            <strong>Test Map 3:</strong> Difference Map (Issue 1 - President)<br>
            <small>Purple-green comparison showing where each performed better</small>
        </a>
        
        <div class="back">
            <a href="/">← Back to Main App</a>
        </div>
    </body>
    </html>
    '''

@app.route('/test/<map_name>')
def serve_test_map(map_name):
    """Serve test interactive maps."""
    from flask import send_file
    import os
    
    map_files = {
        'issue1': PROJECT_ROOT / 'test_map_2023_issue1.html',
        'president': PROJECT_ROOT / 'test_map_2024_president.html',
        'difference': PROJECT_ROOT / 'test_map_difference.html'
    }
    
    if map_name not in map_files:
        return "Map not found", 404
    
    file_path = map_files[map_name]
    if not file_path.exists():
        return f"Map file not found. Run: python scripts/test_interactive_maps.py", 404
    
    return send_file(file_path, mimetype='text/html')

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
    mode = data.get('mode', 'static')  # Default to static for backward compatibility
    
    if not race1_id or not race2_id:
        return jsonify({'error': 'Both races must be selected'}), 400
    
    if race1_id == race2_id:
        return jsonify({'error': 'Please select two different races'}), 400
    
    try:
        if mode == 'interactive':
            maps_html, stats = create_comparison_map_folium(race1_id, race2_id)
            
            if maps_html is None:
                return jsonify({'error': stats}), 500
            
            return jsonify({
                'mode': 'interactive',
                'maps': maps_html,
                'stats': stats
            })
        else:
            img_base64, stats = create_comparison_map_static(race1_id, race2_id)
            
            if img_base64 is None:
                return jsonify({'error': stats}), 500
            
            return jsonify({
                'mode': 'static',
                'image': img_base64,
                'stats': stats
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def extract_progressive_candidate_name(candidates_str):
    """
    Extract the progressive/Democratic candidate's last name from candidates string.
    
    Examples:
        "Vogel (Progressive) vs Ross (Conservative)" -> "Vogel"
        "Harris (D) vs Trump (R)" -> "Harris"
        "Brown (D) vs Moreno (R)" -> "Brown"
    """
    if not candidates_str:
        return None
    
    # Split on 'vs' and take the first candidate
    parts = candidates_str.split(' vs ')
    if not parts:
        return None
    
    # Get first candidate (before "vs")
    first_candidate = parts[0].strip()
    
    # Extract name before parentheses (e.g., "Vogel (Progressive)" -> "Vogel")
    name = first_candidate.split('(')[0].strip()
    
    # If there are multiple words, take the last one as the last name
    name_parts = name.split()
    if name_parts:
        return name_parts[-1]
    
    return None


@app.route('/api/onemap', methods=['POST'])
def api_onemap():
    """API endpoint to generate single map with color scheme selection."""
    data = request.get_json()
    race_id = data.get('race')
    colormap = data.get('colormap', 'RdBu')  # Default to red/blue
    
    if not race_id:
        return jsonify({'error': 'Race must be selected'}), 400
    
    try:
        # Load race data
        gdf, info = load_race_data(race_id)
        
        if gdf is None:
            return jsonify({'error': info}), 500
        
        # Convert to WGS84 for Folium
        gdf = gdf.to_crs('EPSG:4326')
        
        # Convert any Timestamp columns to strings
        for col in gdf.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf[col]):
                gdf[col] = gdf[col].astype(str)
        
        # Get center for map
        bounds = gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Create Folium map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='CartoDB positron')
        
        # Extract progressive candidate's last name for caption
        candidate_name = extract_progressive_candidate_name(info.get('candidates', ''))
        
        # Choose colors based on colormap selection
        if colormap == 'PuOr':
            # Purple (high) to Orange (low) - good for difference maps, no green conflict
            colors = ['#e66101', '#fdb863', '#fee0b6', '#f7f7f7', '#d8daeb', '#b2abd2', '#5e3c99']
            caption = f'{candidate_name} Share' if candidate_name else 'Democratic/Progressive Share'
        elif colormap == 'PiYG':
            # Pink to Yellow-Green - another alternative
            colors = ['#c51b7d', '#e9a3c9', '#fde0ef', '#f7f7f7', '#e6f5d0', '#a1d76a', '#4d9221']
            caption = f'{candidate_name} Share' if candidate_name else 'Democratic/Progressive Share'
        else:  # Default RdBu
            colors = ['#b2182b', '#ef8a62', '#fddbc7', '#f7f7f7', '#d1e5f0', '#67a9cf', '#2166ac']
            caption = 'Democratic/Progressive Share'
        
        colormap_obj = cm.LinearColormap(
            colors=colors,
            vmin=0, vmax=1, caption=caption
        )
        
        folium.GeoJson(
            gdf,
            style_function=lambda feature: {
                'fillColor': colormap_obj(feature['properties']['D_share']) if feature['properties']['D_share'] is not None else 'gray',
                'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['PRECINCT', 'D_share', 'D_votes', 'R_votes', 'total'],
                aliases=['Precinct:', 'Dem/Prog Share:', 'Dem/Prog Votes:', 'Rep/Cons Votes:', 'Total:'],
                localize=True, sticky=False, labels=True,
                style="background-color: white; border: 2px solid black; border-radius: 3px; box-shadow: 3px;",
                max_width=300,
            )
        ).add_to(m)
        colormap_obj.add_to(m)
        plugins.Fullscreen().add_to(m)
        
        # Add title control
        title_control = f'''
        <script>
            window.addEventListener('load', function() {{
                var map = null;
                for (var key in window) {{
                    if (window[key] instanceof L.Map) {{
                        map = window[key];
                        break;
                    }}
                }}
                if (map) {{
                    var titleDiv = null;
                    L.Control.Title = L.Control.extend({{
                        onAdd: function(map) {{
                            titleDiv = L.DomUtil.create('div', 'leaflet-control-title-dynamic');
                            titleDiv.innerHTML = '{info['display_name']}';
                            titleDiv.style.backgroundColor = 'white';
                            titleDiv.style.border = '2px solid grey';
                            titleDiv.style.borderRadius = '4px';
                            titleDiv.style.padding = '10px';
                            titleDiv.style.fontSize = '18px';
                            titleDiv.style.fontWeight = 'bold';
                            titleDiv.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
                            titleDiv.style.maxWidth = '500px';
                            titleDiv.style.display = 'none';
                            return titleDiv;
                        }}
                    }});
                    var titleControl = new L.Control.Title({{ position: 'topleft' }});
                    titleControl.addTo(map);
                    
                    function updateTitleVisibility() {{
                        if (titleDiv) {{
                            var isFullscreen = document.fullscreenElement || 
                                             document.webkitFullscreenElement || 
                                             document.mozFullScreenElement ||
                                             document.msFullscreenElement;
                            titleDiv.style.display = isFullscreen ? 'block' : 'none';
                        }}
                    }}
                    
                    document.addEventListener('fullscreenchange', updateTitleVisibility);
                    document.addEventListener('webkitfullscreenchange', updateTitleVisibility);
                    document.addEventListener('mozfullscreenchange', updateTitleVisibility);
                    document.addEventListener('MSFullscreenChange', updateTitleVisibility);
                    
                    if (map.on) {{
                        map.on('fullscreenchange', updateTitleVisibility);
                    }}
                }}
            }});
        </script>
        '''
        m.get_root().html.add_child(folium.Element(title_control))
        
        # Add CSS for map sizing and colorbar positioning
        fill_css = '''<style>
            html, body {
                width: 100% !important;
                height: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            .folium-map, #map, div.folium-map {
                width: 100% !important;
                height: 100% !important;
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                right: 0 !important;
                bottom: 0 !important;
            }
            .leaflet-top.leaflet-right {
                top: auto !important;
                bottom: 10px !important;
                left: 50% !important;
                right: auto !important;
                transform: translateX(-50%) !important;
            }
        </style>'''
        m.get_root().html.add_child(folium.Element(fill_css))
        
        # Add Home button
        home_button = f'''
        <script>
            window.addEventListener('load', function() {{
                var map = null;
                for (var key in window) {{
                    if (window[key] instanceof L.Map) {{
                        map = window[key];
                        break;
                    }}
                }}
                if (map) {{
                    L.Control.HomeButton = L.Control.extend({{
                        onAdd: function(map) {{
                            var button = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                            button.innerHTML = '🏠';
                            button.style.backgroundColor = 'white';
                            button.style.width = '34px';
                            button.style.height = '34px';
                            button.style.lineHeight = '34px';
                            button.style.textAlign = 'center';
                            button.style.cursor = 'pointer';
                            button.style.fontSize = '18px';
                            button.title = 'Reset to initial view';
                            button.onclick = function() {{
                                map.setView([{center_lat}, {center_lon}], 10);
                            }};
                            return button;
                        }}
                    }});
                    var homeControl = new L.Control.HomeButton({{ position: 'topleft' }});
                    homeControl.addTo(map);
                }}
            }});
        </script>
        '''
        m.get_root().html.add_child(folium.Element(home_button))
        
        # Get HTML
        map_html = m._repr_html_()
        
        # Calculate statistics
        stats = {
            'name': info['display_name'],
            'pct': float(gdf['D_share'].mean() * 100),
            'total_d': int(gdf['D_votes'].sum()),
            'total_r': int(gdf['R_votes'].sum()),
            'total': int(gdf['total'].sum())
        }
        
        return jsonify({
            'map': map_html,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)

