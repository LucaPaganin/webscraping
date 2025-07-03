# WebScraping Projects

This repository contains various web scraping and data processing tools.

## Projects

### House Crawler Chrome Extension
A Chrome extension for interactive web scraping of property listings.

### Real Estate Data Processing

#### Immobiliare.it API Scraper
A flexible scraper for retrieving real estate listings from immobiliare.it and storing them in various formats.

Located in: `immob/api_immobiliare/fetch_ads.py`

Features:
- Scrapes property listings from immobiliare.it API
- Configurable via command-line arguments and environment variables
- Support for multiple cities and contract types (rent/sale)
- Storage options:
  - CSV files
  - SQLite database
  - Azure Cosmos DB
- Configurable pagination and request delays

Setup:
1. Copy `.env.example` to `.env` and fill in your credentials (if using Cosmos DB)
2. Install requirements: `pip install -r immob/api_immobiliare/requirements.txt`

Example usage:
```bash
# Basic usage (saves to CSV by default)
python fetch_ads.py

# Specify city and contract type
python fetch_ads.py --city genova --contract rent

# Fetch multiple pages
python fetch_ads.py --max-pages 5

# Save to SQLite
python fetch_ads.py --save-sqlite --sqlite-path ./my_database.db

# Save to Cosmos DB (requires .env configuration)
python fetch_ads.py --save-cosmos

# Save to JSON file
python fetch_ads.py --save-json

# Combine options
python fetch_ads.py --city savona --contract sale --max-pages 3 --save-sqlite --save-json --output-path ./data
```

See `immob/api_immobiliare/fetch_ads.py --help` for all options.

#### SQLite Helper Functions
The SQLite helper functions provide a convenient way to store and retrieve real estate data from web scraping results.

Located in: `immob/api_immobiliare/sqlite_helpers.py`

Features:
- Initialize SQLite database with the appropriate schema
- Write real estate data from pandas DataFrame to SQLite
- Query data with various filtering options
- Full-text search across multiple columns
- Export data to CSV
- Database statistics and analysis

Example usage:

```python
from api_immobiliare.sqlite_helpers import (
    init_database, write_df_to_sqlite, read_ads_from_sqlite,
    search_ads_by_text, get_database_stats, export_to_csv
)

# Initialize database
init_database("data/immobili.db")

# Load dataframe from a scraping result
import pandas as pd
df = pd.read_csv("browser_use/immobili.csv")

# Write to database
new_records, updated_records = write_df_to_sqlite(df, "data/immobili.db")
print(f"Added {new_records} new records and updated {updated_records} existing records")

# Query data
apartments = read_ads_from_sqlite(
    "data/immobili.db",
    filters={"property_type": "Appartamento | Intera proprietà", "rooms": 2},
    order_by="price ASC",
    limit=10
)
print(f"Found {len(apartments)} apartments with 2 rooms")

# Search by text
search_results = search_ads_by_text(
    "data/immobili.db",
    search_text="mare",
    search_columns=["title", "description"]
)
print(f"Found {len(search_results)} listings mentioning 'mare'")

# Export to CSV
export_to_csv(
    "data/immobili.db",
    "scraping_results/apartments_2_rooms.csv",
    filters={"property_type": "Appartamento | Intera proprietà", "rooms": 2}
)
```

See `immob/api_immobiliare/example_sqlite_usage.py` for a more complete example.

### Other Projects
- eBay scraper
- Vinted scraper
- Ryanair price monitor
- Movie downloader

## Requirements
Each project has its own requirements.txt file in its respective directory.
