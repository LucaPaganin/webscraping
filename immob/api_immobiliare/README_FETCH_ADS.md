# Immobiliare.it Ad Fetcher

This script retrieves real estate ads from Immobiliare.it with flexible options to query either an entire city or zone by zone.

## Features

- **Two Processing Modes**:
  - **Single Query Mode**: Fetch all ads in one query (default)
  - **Zone-by-Zone Mode**: Process each zone separately, saving data between zones
- **Filtering Options**:
  - Filter by city
  - Filter by contract type (rent/sale)
  - Filter by macrozones (areas within a city)
- **Multiple Output Formats**:
  - CSV (default)
  - JSON
  - SQLite database
  - Azure Cosmos DB
- **Zone Exploration**:
  - List available zones and macrozones for a city

## Prerequisites

- Python 3.6+
- Required Python packages:
  ```
  requests
  pandas
  azure-cosmos (optional, for Cosmos DB support)
  python-dotenv
  ```

## Installation

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in a `.env` file (if using Cosmos DB):
   ```
   COSMOS_DB_ACCOUNT_URI=your_cosmos_endpoint
   COSMOS_DB_ACCOUNT_KEY=your_cosmos_key
   COSMOS_DB_DATABASE_NAME=your_cosmos_db
   IMMOBILIARE_API_URL=https://www.immobiliare.it/api-next/search-list/listings/
   PHPSESSID=your_php_session_id
   IMMSESSID=your_imm_session_id
   DATADOME=your_datadome_cookie
   ```

## Basic Usage

### List Available Zones

```bash
python fetch_immobiliare_ads.py --city genova --list-zones
```

### Fetch Rental Ads (Single Query)

```bash
# Fetch 1 page of rental ads for Genova
python fetch_immobiliare_ads.py --city genova --contract rent

# Fetch all pages of rental ads
python fetch_immobiliare_ads.py --city genova --contract rent --max-pages 0
```

### Fetch Ads Zone by Zone

```bash
# Fetch 1 page of rental ads for each zone in Genova
python fetch_immobiliare_ads.py --city genova --contract rent --use-zones

# Fetch all pages of sale ads for each zone
python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0 --use-zones
```

### Filter by Macrozones

```bash
# Using macrozone IDs
python fetch_immobiliare_ads.py --city genova --macrozones 13297 13298

# Using macrozone names
python fetch_immobiliare_ads.py --city genova --macrozone-names centro foce
```

### Save to Different Formats

```bash
# Save to CSV (default), JSON, and SQLite
python fetch_immobiliare_ads.py --city genova --save-csv --save-json --save-sqlite --output-path ./data
```

## Advanced Options

### City Selection

```bash
# Search for a city by name
python fetch_immobiliare_ads.py --comune-query "Milano"

# Specify a commune ID directly
python fetch_immobiliare_ads.py --comune-id "12345" --comune-name "Milano"
```

### Other Options

```bash
# Start from a specific page
python fetch_immobiliare_ads.py --city genova --start-page 3

# Save logs to file
python fetch_immobiliare_ads.py --city genova --log-to-file

# When using zone-by-zone mode, don't save combined results
python fetch_immobiliare_ads.py --city genova --use-zones --no-combined-results
```

## Output Files

- **CSV files**: `ads_[city]_[zone]_[contract]_[timestamp].csv`
- **JSON files**: `ads_[city]_[zone]_[contract]_[timestamp].json`
- **SQLite database**: `ads.db` or `ads_zones.db`
- **Log file** (when using `--log-to-file`): `fetch_ads_[timestamp].log`

## Notes

- When using `--max-pages 0`, the script will fetch all available pages
- Zone-by-zone mode is more reliable for cities with many ads, as it processes zones separately
- You need to configure the `.env` file for Cosmos DB support

## Troubleshooting

- If the API returns 403 errors, you may need to update the cookies in your `.env` file
- If no zones are found for a city, check if the city is correctly supported in the `common_cities.json` file

## Examples

### Example 1: List Available Zones for a City

```bash
python fetch_immobiliare_ads.py --city genova --list-zones
```

### Example 2: Fetch All Sale Ads for Centro and Foce Zones in Genova

```bash
python fetch_immobiliare_ads.py --city genova --contract sale --macrozone-names centro foce --max-pages 0
```

### Example 3: Fetch All Rental Ads Zone by Zone and Save to Multiple Formats

```bash
python fetch_immobiliare_ads.py --city genova --contract rent --use-zones --max-pages 0 --save-csv --save-json --save-sqlite --output-path ./data
```
