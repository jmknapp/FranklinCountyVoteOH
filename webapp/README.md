# Franklin County Vote Analysis - Web App

Interactive web application for comparing precinct-level election results and ballot issues across Franklin County, Ohio.

## Features

- **Interactive Race Selection**: Choose any two races or ballot issues from available data
- **Three-Panel Visualization**: 
  - Left: First selected race/issue (choropleth)
  - Middle: Second selected race/issue (choropleth)
  - Right: Difference map showing precinct-by-precinct variation
- **Detailed Statistics**: Vote totals, percentages, and difference metrics
- **Modern UI**: Clean, responsive design that works on desktop and mobile

## Available Comparisons

The app automatically discovers all available race results including:
- Presidential elections (2020, 2024)
- Governor races (2018, 2022)
- Congressional races by district (2018-2024)
- State ballot issues (2023 Issue 1 - Abortion, Issue 2 - Cannabis)

## Running the App

### 1. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Flask
pip install flask
```

### 2. Start the Server

```bash
# From the project root directory
cd webapp
python app.py
```

The app will start on `http://localhost:5050`

### 3. Open in Browser

Navigate to `http://localhost:5050` in your web browser.

## Usage

1. **Select First Race**: Choose a race or issue from the first dropdown
2. **Select Second Race**: Choose a different race or issue from the second dropdown
3. **Generate Comparison**: Click the "Generate Comparison" button
4. **View Results**: The app will display three maps and detailed statistics

## Color Scheme

- **Blue**: Democratic/Yes votes (pro-choice, pro-cannabis, etc.)
- **Red**: Republican/No votes
- **Difference Map**: 
  - Blue = First race outperformed second
  - Red = Second race outperformed first

## Technical Details

### Backend (`app.py`)
- Flask web server
- Dynamic data loading from CSV files
- On-demand map generation using GeoPandas and Matplotlib
- Automatic shapefile selection based on election year

### Frontend (`templates/index.html`)
- Modern, responsive HTML/CSS/JavaScript
- Fetch API for async requests
- Base64-encoded image display
- Real-time statistics updates

### Data Flow
1. User selects two races
2. Frontend sends POST request to `/api/compare`
3. Backend loads race data and corresponding shapefiles
4. Maps generated using Matplotlib
5. Image encoded as base64 and returned with statistics
6. Frontend displays results

## Performance Notes

- First request may be slower as shapefiles are loaded and cached
- Subsequent requests are faster due to shapefile caching
- Map generation takes 5-15 seconds depending on data size

## Future Enhancements

Potential improvements:
- [ ] Interactive maps using Folium/Leaflet
- [ ] Export functionality (download maps as PNG/PDF)
- [ ] Historical timeline view
- [ ] Precinct search and highlight
- [ ] Mobile app
- [ ] API for programmatic access

## API Endpoints

### GET `/`
Returns the main HTML page with race selection interface.

### GET `/api/races`
Returns JSON array of available races:
```json
[
  {
    "id": "results_2024",
    "year": "2024",
    "type": "president",
    "display_name": "2024 President",
    "file_path": "data/raw/results_2024.csv"
  },
  ...
]
```

### POST `/api/compare`
Request body:
```json
{
  "race1": "results_2024",
  "race2": "results_2023_issue1"
}
```

Response:
```json
{
  "image": "base64_encoded_image_data",
  "stats": {
    "race1": {
      "name": "2024 President",
      "pct": 64.3,
      "total_d": 410234,
      "total_r": 227887
    },
    "race2": {
      "name": "2023 State Issue 1 (Abortion Rights)",
      "pct": 72.9,
      "total_d": 308379,
      "total_r": 114637
    },
    "difference": {
      "mean": 7.9,
      "std": 8.2,
      "min": -63.0,
      "max": 28.6
    }
  }
}
```

## Troubleshooting

**Problem**: App won't start
- **Solution**: Make sure Flask is installed: `pip install flask`

**Problem**: No races appear in dropdowns
- **Solution**: Ensure CSV files exist in `data/raw/` with pattern `results_*.csv`

**Problem**: Maps fail to generate
- **Solution**: Check that corresponding shapefiles exist in `data/raw/precincts_*/`

**Problem**: Slow performance
- **Solution**: First request is slow while caching shapefiles. Subsequent requests are faster.

## License

MIT License - See main project LICENSE file.

