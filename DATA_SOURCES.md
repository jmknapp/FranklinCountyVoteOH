# Data Sources

## Precinct Shapefiles

**Source**: Franklin County Board of Elections  
**URL**: https://vote.franklincountyohio.gov/maps-and-data/gis-shape-files

All precinct boundary shapefiles for Franklin County, Ohio have been downloaded from the official Board of Elections website for years 2006-2024.

### Downloaded Files

```
data/raw/precincts_2024/  # Base year (General Election 2024)
data/raw/precincts_2022/  # General Election 2022
data/raw/precincts_2020/  # General Election 2020
data/raw/precincts_2018/  # General Election 2018
data/raw/precincts_2016/  # General Election 2016
data/raw/precincts_2014/  # General Election 2014
data/raw/precincts_2012/  # General Election 2012
data/raw/precincts_2010/  # General Election 2010
data/raw/precincts_2008/  # General Election 2008
data/raw/precincts_2006/  # General Election 2006
```

Each directory contains:
- `.shp` - Shapefile geometries
- `.shx` - Shapefile index
- `.dbf` - Attribute table
- `.prj` - Projection information (where available)
- `.cpg` - Code page information (where available)

### Coordinate Reference System

The shapefiles use various coordinate systems but are automatically reprojected to:
**EPSG:3734** - NAD83 / Ohio South (ftUS)

This is the standard projection for Franklin County geospatial data.

### Re-downloading Shapefiles

To re-download all shapefiles:

```bash
./scripts/download_shapefiles_curl.sh
```

## Election Results Data

**Source**: Franklin County Board of Elections  
**URL**: https://vote.franklincountyohio.gov/election-info/

Election results must be obtained separately and formatted as CSV files with the following structure:

```csv
PRECINCT,D_votes,R_votes
A001,450,350
A002,520,480
...
```

### Required Fields
- **PRECINCT**: Precinct identifier (must match shapefile)
- **D_votes**: Democratic party votes
- **R_votes**: Republican party votes

### Where to Find Results

1. Visit https://vote.franklincountyohio.gov/election-info/
2. Select the election year
3. Download detailed results by precinct
4. Format as CSV with the required columns
5. Save to `data/raw/results_YYYY.csv`

### Inspecting Field Names

Before running the pipeline, inspect your downloaded shapefiles to determine the correct precinct ID field name:

```bash
# After installing dependencies
python scripts/inspect_shapefiles.py
```

This will show you the actual field names in each shapefile so you can update `config/project.yaml` accordingly.

## Data Attribution

- **Precinct Boundaries**: Franklin County Board of Elections, Columbus, Ohio
- **Election Results**: Franklin County Board of Elections
- **Census Data** (if using population weights): U.S. Census Bureau

## Data License

The precinct shapefiles and election results are public domain data provided by Franklin County, Ohio government.

## Data Updates

The Franklin County Board of Elections updates precinct boundaries periodically, typically:
- After redistricting (every 10 years following Census)
- When municipalities annex territory
- To rebalance precinct sizes

Check the Board of Elections website regularly for updated shapefiles.

## Questions About Data

For questions about precinct boundaries or election results, contact:

**Franklin County Board of Elections**  
1700 Morse Rd  
Columbus, OH 43229  
Phone: 614-525-3100  
Email: https://vote.franklincountyohio.gov/contact

