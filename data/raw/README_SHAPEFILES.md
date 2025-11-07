# Franklin County Precinct Shapefiles

## Source

All shapefiles downloaded from:
**[Franklin County Board of Elections - GIS Shape Files](https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files)**

Downloaded on: November 7, 2025

## Downloaded Years

The following precinct shapefiles have been downloaded and organized:

| Year | Shapefile Name | Directory | Size |
|------|----------------|-----------|------|
| 2025 | Voting_Precinct.shp | `precincts_2025/` | 1.3 MB |
| 2023 | Voting_Precinct.shp | `precincts_2023/` | 1.4 MB |
| 2022 | Voting-Precincts-G22.shp | `precincts_2022/` | 1.3 MB |
| 2020 | Voting-Precincts-G20.shp | `precincts_2020/` | 1.3 MB |
| 2018 | Voting-Precincts-G18.shp | `precincts_2018/` | 1.4 MB |
| 2016 | Voting-Precincts-G16.shp | `precincts_2016/` | 1.4 MB |
| 2014 | Precincts_G14.shp | `precincts_2014/` | 1.4 MB |
| 2012 | Precincts_G12.shp | `precincts_2012/` | 1.5 MB |
| 2010 | Precincts_G10.shp | `precincts_2010/` | 1.4 MB |
| 2009 | Precincts_P09.shp | `precincts_2009/` | 1.5 MB |
| 2008 | Precincts_08.shp | `precincts_2008/` | 1.1 MB |
| 2007 | Precincts_G07.shp | `precincts_2007/` | 1.5 MB |
| 2006 | Precincts_G06.shp | `precincts_2006/` | 551 KB |

## Shapefile Components

Each shapefile directory contains the following files:
- `.shp` - Main shapefile with geometry
- `.shx` - Shape index
- `.dbf` - Attribute table
- `.prj` - Projection information (when available)
- `.sbn`/`.sbx` - Spatial index (when available)
- `.cpg` - Code page file (when available)

## Coordinate Reference System

The shapefiles use various coordinate systems. The project configuration is set to automatically reproject all shapefiles to:

**EPSG:3734 (NAD83 / Ohio South - State Plane)**

This ensures consistent spatial operations across all years.

## Precinct ID Fields

Before running the pipeline, you need to verify the precinct ID field names in each shapefile. Open the `.dbf` files or inspect with QGIS/ArcGIS to determine the correct field names.

Common field names include:
- `PRECINCT`
- `PREC_ID`
- `PRECINCT_ID`
- `NAME`

Update the `id_fields` section in `config/project.yaml` with the correct field names for each year.

## Next Steps

1. **Inspect ID Fields**: Check each shapefile to determine precinct ID field names
   ```bash
   # Using ogrinfo (from GDAL)
   ogrinfo -al -so data/raw/precincts_2025/Voting_Precinct.shp
   ```

2. **Update Config**: Edit `config/project.yaml` to set correct `id_fields` for each year

3. **Add Election Results**: Download election results CSVs and place them in `data/raw/`
   - Results available at: https://vote.franklincountyohio.gov/election-info/
   - Format needed: `PRECINCT_ID,D_votes,R_votes`

4. **Run Pipeline**: After configuration, run:
   ```bash
   python -m src.cli init
   python -m src.cli harmonize-all
   python -m src.cli metrics
   python -m src.cli maps 2025 D_share
   ```

## Re-downloading Shapefiles

To re-download all shapefiles (e.g., if the Board of Elections updates them):

```bash
./scripts/download_shapefiles.sh
```

This will overwrite existing shapefiles with the latest versions from the website.

## Notes

- Some years have slightly different naming conventions (G = General election, P = Primary election)
- Precinct boundaries may have changed between years - this is expected and the pipeline handles it
- The 2006 shapefile is notably smaller, possibly indicating fewer precincts or less detailed boundaries
- Not all years have all auxiliary files (.prj, .cpg, etc.) but the essential files (.shp, .shx, .dbf) are present

## Contact

For questions about the shapefiles or data accuracy, contact:

**Franklin County Board of Elections**  
1700 Morse Rd, Columbus, OH 43229  
Phone: 614-525-3100  
Website: https://vote.franklincountyohio.gov/

