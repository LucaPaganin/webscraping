# WebScraping Projects

This repository contains various web scraping and data processing tools.

## Projects

### House Crawler Chrome Extension
A Chrome extension for interactive web scraping of property listings.

### Real Estate Data Processing

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
