# CSV to Database Uploader

This utility script allows you to upload CSV files containing real estate data to either Cosmos DB or SQLite databases.

## Requirements

Install required packages:

```bash
pip install -r requirements.txt
```

## Setup for Cosmos DB

If you plan to use Cosmos DB, create a `.env` file in the same directory with the following environment variables:

```
COSMOS_DB_ACCOUNT_URI=<your-cosmos-db-endpoint>
COSMOS_DB_ACCOUNT_KEY=<your-cosmos-db-key>
COSMOS_DB_DATABASE_NAME=<your-cosmos-db-name>
```

## Usage

### Basic Usage

```bash
# Upload to Cosmos DB
python upload_csv_to_db.py path/to/your/file.csv --cosmos

# Upload to SQLite
python upload_csv_to_db.py path/to/your/file.csv --sqlite ads.db
```

### Command-Line Arguments

#### Required Arguments:
- Positional arguments: One or more CSV file paths to upload
- Database selection (one required):
  - `--cosmos`: Upload to Cosmos DB
  - `--sqlite DB_PATH`: Upload to SQLite database at the specified path

#### Cosmos DB Options:
- `--container`, `-c`: Name of the Cosmos DB container (default: derived from filename)
- `--city`: City name to use as partition key if missing in records

#### SQLite Options:
- `--table`, `-t`: Name of the SQLite table (default: derived from filename)
- `--if-exists`: How to behave if the table already exists ('fail', 'replace', 'append')
- `--by-province`: Create separate tables for each province (table name will be suffixed with province name)

#### Common Options:
- `--batch-size`, `-b`: Number of records to upload in a single batch (default: 50)
- `--report`, `-r`: Generate a detailed JSON report after upload

### Examples

#### Upload a CSV file to Cosmos DB:
```bash
python upload_csv_to_db.py ads_genova_rent.csv --cosmos --container ads_rent
```

#### Upload multiple CSV files to Cosmos DB:
```bash
python upload_csv_to_db.py ads_genova_rent.csv ads_milano_rent.csv --cosmos
```

#### Upload a CSV file to SQLite:
```bash
python upload_csv_to_db.py ads_genova_rent.csv --sqlite real_estate.db --table genova_rentals
```

#### Replace existing SQLite table:
```bash
python upload_csv_to_db.py ads_genova_rent.csv --sqlite real_estate.db --if-exists replace
```

#### Create province-specific tables in SQLite:
```bash
python upload_csv_to_db.py ads_multiple_provinces.csv --sqlite real_estate.db --by-province
```

#### Generate a detailed report:
```bash
python upload_csv_to_db.py ads_genova_rent.csv --sqlite real_estate.db --report
```

## Output

- The script logs progress to the console.
- If `--report` is specified, a detailed JSON report is saved to the current directory.
- When using `--by-province`, separate tables will be created for each province in the data.

## Table Structure

- For SQLite uploads, the table structure matches the CSV columns.
- For SQLite with `--by-province`, tables named `{base_table_name}_{province}` will be created.
- For Cosmos DB, records are stored with the city as the partition key.

## Notes

- The script handles batching to improve performance with large datasets.
- NaN values and empty strings are properly converted to NULL in the database.
- The script will create parent directories for SQLite files if they don't exist.
