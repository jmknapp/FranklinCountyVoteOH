# Census Demographics Integration

## Overview

The Franklin County Vote Analysis project now includes comprehensive Census demographic data integrated at the precinct level. This allows for rich analysis of how demographic factors correlate with voting patterns.

## Data Sources

### 2020 Census Blocks
- **19,027 Census blocks** in Franklin County
- Source: TIGER/Line Shapefiles (U.S. Census Bureau)
- Used for precise geographic crosswalks

### 2020 ACS 5-Year Demographics
- **952 block groups** in Franklin County with demographic data
- Source: American Community Survey (U.S. Census API)
- Aggregated to precinct level using population-weighted spatial overlay

### Demographic Variables

- **Total Population**: Number of residents per precinct
- **Median Household Income**: Income in dollars
- **Median Age**: Age in years
- **% College Degree**: Percentage with bachelor's degree or higher
- **% White (Non-Hispanic)**: Racial composition
- **% Black**: Racial composition
- **% Hispanic**: Ethnic composition

## Key Findings

### 2024 Presidential Election

**Strongest Correlations with Democratic Vote Share:**
- **% Black**: +0.542 (strong positive)
- **% White (NH)**: -0.507 (strong negative)
- **Median Income**: -0.316 (moderate negative)
- **Median Age**: -0.242 (weak negative)

**Demographic Voting Blocs (by D% support):**
1. Low Income, Low Education, Majority Black: **79.3%**
2. High Income, High Education, Majority White: **63.3%**
3. Low Income, Low Education, Majority White: **54.7%**
4. High Income, Low Education, Majority White: **51.7%**

### 2023 Abortion Rights (Issue 1)

**Key Differences from Presidential:**
- **% College Degree**: +0.172 (positive correlation, unlike presidential)
- More uniform support across demographic groups (64-82% "Yes")
- Education level mattered more than for presidential race
- Income was less predictive than for presidential race

**Demographic Voting Blocs (by Yes% support):**
1. Low Income, High Education, Majority White: **79.3%**
2. Low Income, Low Education, Majority Black: **77.8%**
3. High Income, High Education, Majority White: **73.1%**
4. High Income, Low Education, Majority White: **64.1%**

## Scripts

### 1. Download Census Data
```bash
python scripts/download_census_data.py
```

Downloads:
- Census block shapefiles (TIGER/Line 2020)
- Block group shapefiles (TIGER/Line 2020)
- ACS 5-year demographic data (2020)
- Merges demographics with geography

Output: `data/raw/census/franklin_county_demographics_2020.gpkg`

### 2. Aggregate to Precincts
```bash
python scripts/aggregate_demographics_to_precincts.py
```

Uses spatial overlay to:
- Find block groups intersecting each precinct
- Calculate population-weighted demographic averages
- Save precinct-level demographics

Output: `data/processed/demographics_by_precinct_2025.csv`

### 3. Analyze Correlations
```bash
python scripts/analyze_demographic_correlations.py
```

Generates:
- Correlation heatmaps
- Scatter plots with regression lines
- Demographic voting bloc analysis

Output: PNG images in `data/processed/demographic_analysis/`

## Web Application

### Demographics Page
Access at: `http://localhost:5050/demographics`

**Features:**
1. **Interactive Demographic Map**
   - Select any race/issue
   - Choose demographic variable to display
   - Map colored by demographic, tooltip shows vote share
   - Displays correlation coefficient

2. **Static Analysis Visualizations**
   - Correlation heatmaps
   - Scatter plots with R² values
   - Demographic bloc bar charts

## Technical Details

### Spatial Aggregation Method

Demographics are aggregated from block groups to precincts using:

1. **Spatial Overlay**: Find all block group/precinct intersections
2. **Area Weighting**: Calculate intersection area as fraction of total block group area
3. **Population Weighting**: Weight demographic values by population in each intersection
4. **Aggregation**: Sum weighted values to get precinct-level estimates

### Data Quality

- **Coverage**: 889 out of 889 precincts (100%) have demographic data
- **Total Population**: 1,304,715 (matches Census county total)
- **Missing Data**: Some precincts have negative median income values (coded as missing), these are filtered out in analysis

### API Endpoints

#### `/api/demographics_map`
POST endpoint for interactive demographic maps

**Request:**
```json
{
  "race": "results_2024",
  "demo_var": "median_income"
}
```

**Response:**
```json
{
  "map": "<HTML>",
  "stats": {
    "race_name": "2024 Presidential",
    "demo_var": "Median Income",
    "correlation": -0.316,
    "n_precincts": 743,
    "demo_min": 12500,
    "demo_max": 248995,
    "demo_median": 58920
  }
}
```

#### `/api/demographic_image/<filename>`
GET endpoint to serve static analysis images

## Insights

### Income Paradox
Higher-income precincts tend to vote *less* Democratic in presidential races (-0.316 correlation), but this reverses somewhat for ballot issues like abortion rights where education becomes more important.

### Education Effect
Education shows minimal correlation with presidential voting (+0.006) but becomes significant for abortion rights (+0.172), suggesting educated voters split their tickets based on issue content.

### Racial Patterns
The strongest predictor of Democratic presidential voting is % Black population (+0.542), followed by % White (NH) in the opposite direction (-0.507).

### Issue vs. Partisan Differences
Ballot issues show weaker demographic polarization than partisan races. The abortion rights issue saw support ranging from 64-82% across demographic blocs, compared to 52-79% for presidential.

## Future Analysis Ideas

1. **Time Series**: Track demographic correlations over multiple elections
2. **Multivariate Models**: Use regression to predict vote share from demographics
3. **Demographic Shift Analysis**: Compare precinct demographics 2010 vs 2020
4. **Ecological Inference**: Estimate voting by demographic subgroups within precincts
5. **Redistricting Analysis**: Use demographics to evaluate proposed district maps

## Data Citations

- U.S. Census Bureau (2020). TIGER/Line Shapefiles. https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- U.S. Census Bureau (2020). American Community Survey 5-Year Data. https://www.census.gov/programs-surveys/acs

## Dependencies

Added to `requirements.txt`:
- `seaborn>=0.12.0` - Statistical visualizations

All other dependencies were already present for geospatial analysis.

---

**Last Updated**: November 9, 2025

