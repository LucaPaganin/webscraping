# Real Estate Ads Fetcher

A script to fetch real estate ads from the Immobiliare.it API and save them in different formats.

## Requirements

Install required packages:

```bash
pip install -r requirements.txt
```

## Setup

1. Create a `.env` file in the same directory as `fetch_ads.py` (see example.env)
2. Add the following environment variables:
   ```
   COSMOS_DB_ACCOUNT_URI=<your-cosmos-db-endpoint>
   COSMOS_DB_ACCOUNT_KEY=<your-cosmos-db-key>
   COSMOS_DB_DATABASE_NAME=<your-cosmos-db-name>
   IMMOBILIARE_API_URL=https://www.immobiliare.it/api-next/search-list/listings/
   PHPSESSID=<your-phpsessid>
   IMMSESSID=<your-immsessid>
   DATADOME=<your-datadome>
   ```

## Usage

### Basic Usage

```bash
python fetch_ads.py
```

This will fetch rental ads for Genova with default settings.

### Command-Line Parameters

#### Location Parameters:
- `--city`, `-c`: City to search for ads (default: genova)
- `--comune-query`: Search query to find a comune by name (will override --city)
- `--comune-id`: Specify idComune directly (will override --city and --comune-query)
- `--comune-name`: Name of the comune when specifying comune-id
- `--macrozones`: List of macrozone IDs to filter results (e.g., --macrozones 10001 10002)
- `--macrozone-names`: List of macrozone names to filter results (e.g., --macrozone-names centro foce)
- `--list-macrozones`: List available macrozones for the selected city and exit

#### Contract and Pagination:
- `--contract`, `-t`: Contract type: rent or sale (default: rent)
- `--max-pages`, `-m`: Maximum number of pages to fetch (default: 1)
- `--start-page`, `-s`: Page to start fetching from (default: 1)

#### Output Parameters:
- `--output-path`, `-o`: Path where to save the output files (default: current directory)
- `--no-save-cosmos`: Do not save data to Cosmos DB
- `--save-sqlite`: Save data to SQLite database
- `--save-csv`: Save data to CSV file (default: True)
- `--save-json`: Save data to JSON file as a list of dictionaries
- `--sqlite-path`: Path to SQLite database file (default: output-path/ads.db)

### Examples

#### Fetch rental ads for Genova and save them to a CSV file:
```bash
python fetch_ads.py --city genova --contract rent --max-pages 5 --save-csv
```

#### Search for comune by name:
```bash
python fetch_ads.py --comune-query "Milano" --contract sale --max-pages 2 --save-json
```

#### Use a specific comune ID:
```bash
python fetch_ads.py --comune-id "8042" --comune-name "Milano" --contract rent --save-sqlite
```

#### Save data in multiple formats:
```bash
python fetch_ads.py --city genova --save-csv --save-json --save-sqlite
```

#### List available macrozones for a city:
```bash
python fetch_ads.py --city genova --list-macrozones
```

#### Filter by macrozones using IDs:
```bash
python fetch_ads.py --city genova --macrozones 10001 10003 --contract rent
```

#### Filter by macrozones using names:
```bash
python fetch_ads.py --city genova --macrozone-names centro castelletto --contract rent
```

## Output

The script will output files in the following formats, depending on the command-line arguments:
- CSV: `ads_<city>_<contract_type>.csv`
- JSON: `ads_<city>_<contract_type>.json`
- SQLite: `ads.db` (or the path specified by `--sqlite-path`)
- Cosmos DB: Container named `ads_<contract_type>`

## Notes

- The script uses random delays between requests to avoid being blocked by the server.
- The script will stop if it reaches the maximum number of pages or if there's an error.
- Macrozone filtering allows you to narrow down your search to specific areas within a city.
- Use `--list-macrozones` to see available macrozones for your selected city.
- For each city, macrozones are defined in `common_cities.json` file.
