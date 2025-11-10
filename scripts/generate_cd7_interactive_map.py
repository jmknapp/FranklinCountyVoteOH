#!/usr/bin/env python3
"""
Generate an interactive Folium map for Columbus City Council District 7 race.
Embeddable in the HTML analysis page.
"""

import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Fullscreen
import json

def main():
    print("Loading data...")
    
    # Load 2025 shapefile
    shapefile = gpd.read_file('data/raw/precincts_2025/VotingPrecinct.shp')
    
    # Ensure CRS
    if shapefile.crs is None:
        shapefile.set_crs('EPSG:3735', inplace=True)
    shapefile = shapefile.to_crs('EPSG:4326')
    
    # Load CD7 results
    results = pd.read_csv('data/raw/results_2025_columbus_cd7.csv')
    results['PRECINCT'] = results['PRECINCT'].str.strip().str.upper()
    
    # Calculate shares
    results['vogel_share'] = results['D_votes'] / (results['D_votes'] + results['R_votes'])
    results['total_votes'] = results['D_votes'] + results['R_votes']
    
    # Merge
    shapefile['PRECINCT'] = shapefile['NAME'].str.strip().str.upper()
    merged = shapefile.merge(results[['PRECINCT', 'D_votes', 'R_votes', 'vogel_share', 'total_votes']], 
                             on='PRECINCT', how='left')
    
    # Filter to Columbus only
    columbus_precincts = merged[merged['NAME'].str.contains('COLUMBUS', case=False, na=False)].copy()
    
    print(f"Merged {len(columbus_precincts)} Columbus precincts")
    
    # Calculate center
    bounds = columbus_precincts.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='CartoDB positron'
    )
    
    # Add fullscreen button
    Fullscreen(position='topleft').add_to(m)
    
    # Create color scale (purple = Ross, orange = Vogel, white = 50-50)
    def get_color(vogel_share):
        if pd.isna(vogel_share):
            return '#cccccc'
        
        if vogel_share >= 0.5:
            # Vogel side: white to orange
            intensity = (vogel_share - 0.5) * 2  # 0 to 1
            r = 255
            g = int(255 - intensity * 105)  # 255 to 150
            b = int(255 - intensity * 205)  # 255 to 50
        else:
            # Ross side: white to purple
            intensity = (0.5 - vogel_share) * 2  # 0 to 1
            r = int(255 - intensity * 97)   # 255 to 158
            g = int(255 - intensity * 195)  # 255 to 60
            b = int(255 - intensity * 105)  # 255 to 150
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # Add choropleth layer
    for idx, row in columbus_precincts.iterrows():
        vogel_share = row['vogel_share']
        precinct_name = row['NAME']
        
        if pd.notna(vogel_share):
            vogel_pct = vogel_share * 100
            ross_pct = 100 - vogel_pct
            tooltip_text = f"""
            <b>{precinct_name}</b><br>
            Vogel: {row['D_votes']:,.0f} ({vogel_pct:.1f}%)<br>
            Ross: {row['R_votes']:,.0f} ({ross_pct:.1f}%)<br>
            Total votes: {row['total_votes']:,.0f}
            """
        else:
            tooltip_text = f"<b>{precinct_name}</b><br>No data"
        
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, color=get_color(vogel_share): {
                'fillColor': color,
                'color': '#666666',
                'weight': 0.5,
                'fillOpacity': 0.5  # Reduced from 0.7 to 0.5 for better street visibility
            },
            tooltip=folium.Tooltip(tooltip_text)
        ).add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: auto;
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <div style="display:flex; height:20px; margin-bottom:5px;">
            <div style="flex:1; background: linear-gradient(to right, #9e3c96, #ffffff, #ff9632);"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:10px;">
            <span><b>Ross</b></span>
            <span><b>Vogel</b></span>
        </div>
        <hr style="margin:10px 0;">
        <p style="margin:0; font-size:12px; color:#666;">
            <b>Results:</b><br>
            Ross: 53,291 (50.8%)<br>
            Vogel: 51,670 (49.2%)
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add home button via JavaScript after map is initialized
    home_button_js = f"""
    <script>
    // Wait for map to be fully initialized
    document.addEventListener('DOMContentLoaded', function() {{
        // Find the map object
        var mapElements = document.querySelectorAll('[id^="map_"]');
        if (mapElements.length > 0) {{
            var mapId = mapElements[0].id;
            var map = window[mapId];
            
            // Add home button control
            L.Control.HomeButton = L.Control.extend({{
                onAdd: function(map) {{
                    var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                    container.innerHTML = '<a href="#" title="Reset view" style="font-size:18px;line-height:30px;width:30px;height:30px;display:block;text-align:center;text-decoration:none;color:#333;background:white;">🏠</a>';
                    container.onclick = function(){{
                        map.setView([{center_lat}, {center_lon}], 11);
                        return false;
                    }};
                    return container;
                }},
                onRemove: function(map) {{}}
            }});
            
            L.control.homeButton = function(opts) {{
                return new L.Control.HomeButton(opts);
            }};
            
            L.control.homeButton({{ position: 'topleft' }}).addTo(map);
        }}
    }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(home_button_js))
    
    # Save
    output_path = 'docs/cd7_election_map.html'
    m.save(output_path)
    print(f"Map saved to: {output_path}")
    
    # Also save a standalone version
    standalone_path = 'data/processed/maps/cd7_election_interactive.html'
    m.save(standalone_path)
    print(f"Standalone map saved to: {standalone_path}")

if __name__ == '__main__':
    main()

