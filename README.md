# Letterboxd World Map

A web app that visualizes which countries your watched films come from by coloring an interactive world map.

## Features

- **Two input methods**: enter a Letterboxd username to scrape your profile, or upload your Letterboxd data export (CSV or ZIP)
- **Interactive choropleth map**: countries colored by film count using a green sequential scale
- **Hover tooltips**: see the country name and exact film count
- **Zoom and pan**: scroll to zoom in, drag to pan around the map
- **Real-time progress**: a progress bar shows TMDb lookup status as films are processed
- **SQLite cache**: TMDb results are cached locally so repeat lookups are instant

## Prerequisites

- Python 3.10+
- A free [TMDb API key](https://www.themoviedb.org/settings/api) (sign up at themoviedb.org)

## Setup

```bash
# Clone the repo
cd Letterboxd-map

# Install dependencies
pip install -r requirements.txt

# Set your TMDb API key
# On Windows (PowerShell):
$env:TMDB_API_KEY = "your_api_key_here"
# On macOS/Linux:
export TMDB_API_KEY="your_api_key_here"

# Run the app
python app.py
```

Open http://localhost:5000 in your browser.

## Usage

### Option 1: By Username
Enter any public Letterboxd username and click **Generate Map**. The app scrapes their watched films and looks up each one on TMDb.

### Option 2: Upload CSV / ZIP
1. Go to your [Letterboxd export page](https://letterboxd.com/settings/data/) and download your data
2. Upload the `.zip` file directly, or extract it and upload `watched.csv`

Processing time depends on the number of films. TMDb lookups are rate-limited to ~4/second, so a 500-film library takes about 4 minutes on the first run. Subsequent runs are much faster thanks to the SQLite cache.

## Project Structure

```
Letterboxd-map/
  app.py                  Flask app and API routes
  config.py               TMDb API key and cache path config
  requirements.txt        Python dependencies
  services/
    csv_parser.py          Letterboxd CSV/ZIP parser
    scraper.py             Letterboxd profile scraper
    tmdb.py                TMDb API client with rate limiting
    cache.py               SQLite cache for TMDb results
    aggregator.py          Country count aggregation + ISO code mapping
  static/
    js/map.js              D3.js map rendering, tooltips, zoom
    css/style.css          Dark theme styling
    data/world-110m.json   TopoJSON world map geometry
  templates/
    index.html             Main page template
```
