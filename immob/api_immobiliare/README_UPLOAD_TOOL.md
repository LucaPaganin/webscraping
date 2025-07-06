# Real Estate Data Upload Tool

This tool provides a unified interface for uploading real estate data from CSV files to various storage destinations using the RealEstateDataManager.

## Features

- Upload CSV files to multiple destinations:
  - SQLite database
  - Azure Cosmos DB
  - JSON files
  - Processed CSV files
- Batch processing to handle large files
- Automatic metadata extraction from filenames
- Detailed reporting and error tracking
- Support for processing multiple files and directories

## Usage

```bash
# Upload to SQLite database
python upload_data.py path/to/data.csv --sqlite real_estate.db

# Upload to Cosmos DB
python upload_data.py path/to/data.csv --cosmos --container ads_collection

# Save to JSON files
python upload_data.py path/to/data.csv --json --output-dir output/

# Process multiple files
python upload_data.py data/*.csv --sqlite real_estate.db

# Process with custom batch size
python upload_data.py large_data.csv --sqlite real_estate.db --batch-size 100

# Generate detailed report
python upload_data.py data/*.csv --sqlite real_estate.db --report
```

## Command-line Arguments

### Input Files
- `csv_files`: Path(s) to CSV file(s) to upload. Can include directories or glob patterns.

### Output Format Selection (choose one)
- `--cosmos`: Upload to Cosmos DB
- `--sqlite DB_PATH`: Upload to SQLite database at the specified path
- `--json`: Save to JSON files
- `--csv`: Save to CSV files (useful for transformations)

### Cosmos DB Options
- `--container`: Name of the Cosmos DB container (default: derived from filename)
- `--city`: City name to use as partition key if missing in records

### SQLite Options
- `--table`: Name of the SQLite table (default: ads)

### File Output Options
- `--output-dir`: Directory to save output files (default: current directory)

### Common Options
- `--batch-size`, `-b`: Number of records per batch (default: 50)
- `--report`, `-r`: Generate a detailed JSON report after upload
- `--config`, `-c`: Path to configuration file

## Examples

### Upload Multiple CSV Files to SQLite

```bash
python upload_data.py data/genova_*.csv --sqlite real_estate.db --table genova_ads
```

### Upload to Cosmos DB with Custom Container

```bash
python upload_data.py data/milano_rent.csv --cosmos --container milano_rentals
```

### Process an Entire Directory

```bash
python upload_data.py data/ --sqlite all_cities.db --batch-size 200 --report
```

## Integration with RealEstateDataManager

This tool uses the `RealEstateDataManager` class internally, providing a command-line interface to the same functionality used for real-time data collection. This ensures consistent data processing logic while offering additional batch processing capabilities.

## Note on File Naming Conventions

The tool attempts to extract metadata (city, contract_type) from filenames using the following patterns:
- `ads_genova_rent.csv` → city: genova, contract_type: rent
- `genova_rent_20230101.csv` → city: genova, contract_type: rent
- `milano_sale_apartments.csv` → city: milano, contract_type: sale

Using these naming conventions helps the tool automatically set appropriate container names and partition keys.
