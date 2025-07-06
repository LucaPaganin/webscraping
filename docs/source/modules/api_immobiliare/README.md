# API Immobiliare Documentation

This folder contains comprehensive documentation for the Python modules in the `api_immobiliare` package.

## Module Overview

The API Immobiliare package provides tools for:

1. **Data Collection**: Scraping real estate listings from immobiliare.it
2. **Data Processing**: Cleaning and transforming the collected data
3. **Data Storage**: Saving data to various formats (CSV, JSON, SQLite, Cosmos DB)
4. **Data Analysis**: Analyzing and visualizing real estate data

## Key Modules

- `fetch_immobiliare_ads.py`: The main scraping tool with zone-by-zone capabilities
- `helpers.py`: Core utility functions and data models
- `sqlite_helpers.py`: Tools for SQLite database operations
- `upload_csv_to_db.py`: Tools for uploading data to databases
- `analyze_real_estate_data.py`: Analysis and visualization tools
- `filter_utils.py`: Data filtering and cleaning utilities

## Usage Example

A typical workflow using these modules:

1. Collect data using `fetch_immobiliare_ads.py`:

```bash
python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0 --use-zones --region lig --save-json --save-csv
```

2. Upload data to databases using `upload_csv_to_db.py`:

```bash
python upload_csv_to_db.py --directory data/ --container ads_sale --sqlite ./ads.db --cosmos
```

3. Analyze data using `analyze_real_estate_data.py` functions.

## Dependencies

- pandas, numpy: For data manipulation
- requests: For HTTP requests
- azure.cosmos: For Cosmos DB operations
- sqlite3: For SQLite database operations
- matplotlib, seaborn: For data visualization
