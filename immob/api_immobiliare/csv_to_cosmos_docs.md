# CSV to Cosmos DB Uploader

This script allows you to upload one or more CSV files containing real estate ads to Azure Cosmos DB.

## Prerequisites

1. Make sure you have set up the required environment variables in your `.env` file:
   ```
   COSMOS_DB_ACCOUNT_URI=your_cosmos_db_endpoint
   COSMOS_DB_ACCOUNT_KEY=your_cosmos_db_key
   COSMOS_DB_DATABASE_NAME=your_cosmos_db_name
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Basic usage:
```
./upload_csv_to_cosmos.py path/to/your/file.csv
```

Upload multiple files:
```
./upload_csv_to_cosmos.py file1.csv file2.csv file3.csv
```

### Options

- `--container`, `-c`: Specify the Cosmos DB container name
  - If not provided, tries to derive it from the filename using format `ads_CITY_CONTRACT.csv`
  - Example: For file `ads_genova_rent.csv`, uses container `ads_rent`

- `--city`: Specify a default city name to use as partition key for records missing this field
  - If not provided, tries to extract from filename or uses "unknown"

- `--batch-size`, `-b`: Number of records to upload in a single batch (default: 50)
  - Increase for faster uploads with stable connections
  - Decrease if you encounter connection issues

- `--report`, `-r`: Generate a detailed JSON report after upload
  - Includes statistics and errors for each file processed

### Examples

Upload a single file to a specific container:
```
./upload_csv_to_cosmos.py --container ads_rent path/to/ads_genova_rent.csv
```

Upload multiple files with a specified city and generate a report:
```
./upload_csv_to_cosmos.py --city genova --report ads_genova_rent.csv ads_genova_sale.csv
```

Upload with a larger batch size for faster processing:
```
./upload_csv_to_cosmos.py --batch-size 100 ads_genova_rent.csv
```

## Handling Errors

- The script provides detailed logging of progress and errors
- If the `--report` option is used, a detailed JSON report is generated
- Upload operations are performed in batches to minimize the impact of failures
- Each record has its own try/except block, so one failed record won't affect others

## Notes

- The script expects CSV files in the same format produced by `fetch_ads.py`
- Each record needs a unique ID and a city field for the partition key
- Missing IDs will be auto-generated using UUID
- Missing city values will be populated using the provided `--city` parameter or extracted from the filename
