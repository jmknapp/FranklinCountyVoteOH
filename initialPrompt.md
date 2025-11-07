You are a senior geospatial engineer. Create a production-quality Python project to analyze precinct-level partisan shifts in Franklin County, Ohio (2006→present). I have yearly precinct shapefiles and CSV results with D/R votes by precinct per year. Some boundaries change across years. I want a pipeline that:

1) Ingests shapefiles + CSVs per year
2) Builds spatial crosswalks between any year Y and a selected base geography (default = latest year’s precincts)
3) Reallocates historical votes onto the base geography using overlap weights (area OR optional population if block weights provided)
4) Produces harmonized time-series tables per base-precinct (two-party shares, swings)
5) Exports: GeoPackage, CSVs, and quick maps (PNG) plus an optional interactive Leaflet/folium HTML
6) Includes solid logging, tests, and a small synthetic dataset for CI

### Tech choices
- Python 3.11
- GeoPandas, pandas, shapely (v2), pyproj, rtree, tqdm, matplotlib, folium
- Optional: contextily, mapclassify
- CLI with Typer; config via YAML
- Testing with pytest
- Formatting: black + ruff

### Repo layout
franklin-shifts/
  README.md
  pyproject.toml            # deps + tool config
  requirements.txt          # mirror deps for quick pip install
  .gitignore
  .env.example              # DATA_DIR=...  OUTPUT_DIR=...
  config/
    project.yaml            # paths, base_year, file patterns, id fields
  data/
    raw/                    # user-provided shp/csv by year
    interim/
    processed/
    examples/               # tiny synthetic demo
  src/
    __init__.py
    io_utils.py             # load_shapefile, load_results, ensure_crs, safe_read_csv
    crosswalk.py            # build_crosswalk(past_gdf, base_gdf, weight=area|pop)
    harmonize.py            # reallocate_votes_to_base(year)
    metrics.py              # compute D_share, swing, turnout, aggregates
    visualize.py            # static maps (PNG), interactive folium map
    cli.py                  # Typer app with commands below
  tests/
    test_crosswalk.py
    test_harmonize.py
    test_metrics.py
  Makefile                  # convenience targets (setup, lint, test, demo)

### Config (config/project.yaml) example
base_year: 2024
crs: "EPSG:3734"   # NAD83 / Ohio South (or use what’s correct for your files)
id_fields:
  2024: PREC_ID
  2022: PREC_ID
  2018: PREC_ID
  2016: PREC_ID
  2012: PREC_ID
  2010: PREC_ID
  2008: PREC_ID
  2006: PREC_ID
paths:
  shapefiles:
    "2024": "data/raw/precincts_2024/precincts_2024.shp"
    "2022": "data/raw/precincts_2022/precincts_2022.shp"
    "2018": "data/raw/precincts_2018/precincts_2018.shp"
    "2016": "data/raw/precincts_2016/precincts_2016.shp"
    "2012": "data/raw/precincts_2012/precincts_2012.shp"
    "2010": "data/raw/precincts_2010/precincts_2010.shp"
    "2008": "data/raw/precincts_2008/precincts_2008.shp"
    "2006": "data/raw/precincts_2006/precincts_2006.shp"
  results_csv:
    "2024": "data/raw/results_2024.csv"
    "2022": "data/raw/results_2022.csv"
    ...
# Optional: block weights to prefer population weighting
weights:
  blocks_gpkg: null  # e.g., "data/raw/oh_blocks.gpkg"
  block_pop_field: null
  block_year_map: {} # map each precinct-year layer to its block layer if needed

### CLI (Typer) commands
- `ffs init`                         : validate config, env, and deps
- `ffs crosswalk --year 2008`        : build 2008→base crosswalk (area weights by default)
- `ffs crosswalk --year 2008 --weight pop` : use block population weights if configured
- `ffs harmonize --year 2008`        : reallocate 2008 votes onto base precincts, write GPKG+CSV
- `ffs harmonize-all`                : loop all non-base years
- `ffs metrics`                      : compute per-precinct D_share, swing (year-over-year & vs base), turnout
- `ffs maps --year 2024 --metric swing_2008_to_2024` : export PNG and an interactive HTML
- `ffs summary`                      : countywide aggregates + trend CSVs
- `ffs demo`                         : run pipeline on tiny synthetic example for tests/CI

### Implementation notes
- Always reproject layers to config.crs on load. Assert identical CRS before overlay.
- Use shapely 2.0 vectorized ops; build spatial index (rtree) before overlay.
- Intersection for crosswalk: past ∩ base → compute overlap fraction.
  - Area weights: frac = area(intersection)/area(past)   (guard against slivers, tol=1e-9)
  - Pop weights (optional): intersect blocks with both layers, allocate by population ratios.
- Vote reallocation: for each base_id, sum past_votes * frac across overlaps.
  - Outputs: per base_id per year: D_votes, R_votes, total_two_party, D_share.
- Robustness: handle missing precincts, zero or null totals, and name mismatches (trim/upper).
- Logging: tqdm progress bars; informative warnings when overlap < 98% or missing ids.
- Performance: chunk large overlays by tiling or spatial index join; avoid exploding memory.

### File formats/output
- GeoPackage: data/processed/harmonized.gpkg
  - Layer per year on base geometry (e.g., `yr_2006_on_2024`)
- CSVs:
  - data/processed/timeseries_per_precinct.csv (wide and long)
  - data/processed/county_aggregates.csv
- Maps:
  - data/processed/maps/  (PNG choropleths)
  - data/processed/interactive/  (folium HTML)

### Minimal code scaffolds to generate
- src/io_utils.py:
  - load_shapefile(path, crs) → GeoDataFrame
  - load_results_csv(path, id_field) → DataFrame with columns [precinct_id, D_votes, R_votes, total]
  - ensure_id_consistency(df, id_field) → normalized id strings
- src/crosswalk.py:
  - build_crosswalk(past_gdf, base_gdf, past_id, base_id, weight="area", blocks_gdf=None, block_pop_field=None) → DataFrame with columns [past_id, base_id, frac]
- src/harmonize.py:
  - reallocate_votes_to_base(year, cfg) → writes GPKG layer + CSV; returns DataFrame
  - harmonize_all(cfg)
- src/metrics.py:
  - compute_two_party_metrics(df_long) → adds D_share, swing_yoy, swing_vs_year
  - county_aggregates(df_long) → turnout, two-party share per year
- src/visualize.py:
  - export_static_choropleth(base_gdf, metric_col, title, out_png)
  - export_folium_map(base_gdf, metric_col, out_html)
- src/cli.py:
  - Typer app wiring commands to functions above

### Tests
- tests/test_crosswalk.py: synthetic squares split 60/40 → expected fracs
- tests/test_harmonize.py: two precincts, simple votes, verify reallocation sums
- tests/test_metrics.py: check D_share and swing math

### README quickstart
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- Copy `.env.example` → `.env`, set DATA_DIR and OUTPUT_DIR
- Put your SHPs and CSVs under data/raw per config
- `python -m src.cli init`
- `python -m src.cli harmonize-all`
- `python -m src.cli metrics`
- `python -m src.cli maps --year 2024 --metric swing_2008_to_2024`

Please generate all files with working boilerplate, including pyproject.toml, requirements.txt, and example synthetic data. Use defensive coding (try/except with helpful messages). Prefer vectorized geospatial ops; avoid per-row Python loops for intersections. Ensure scripts run end-to-end with the synthetic example via `ffs demo`.
