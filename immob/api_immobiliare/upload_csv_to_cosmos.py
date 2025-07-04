#!/usr/bin/env python3
# --- upload_csv_to_cosmos.py ---

import os
import sys
import json
import uuid
import argparse
import logging
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from helpers import init_cosmos_client

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_env_vars():
    """Load environment variables from .env file"""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    
    # Get environment variables with fallbacks
    env_vars = {
        "COSMOS_ENDPOINT": os.environ.get("COSMOS_DB_ACCOUNT_URI", ""),
        "COSMOS_KEY": os.environ.get("COSMOS_DB_ACCOUNT_KEY", ""),
        "COSMOS_DB": os.environ.get("COSMOS_DB_DATABASE_NAME", "")
    }
    
    return env_vars

def validate_config(config):
    """Validate configuration has required values"""
    missing = []
    
    if not config.get("cosmos_endpoint"):
        missing.append("COSMOS_DB_ACCOUNT_URI")
    if not config.get("cosmos_key"):
        missing.append("COSMOS_DB_ACCOUNT_KEY")
    if not config.get("cosmos_db"):
        missing.append("COSMOS_DB_DATABASE_NAME")
    
    if missing:
        logger.error(f"[ERROR] Missing environment variables: {', '.join(missing)}")
        logger.error("[ERROR] Please set these variables in the .env file")
        return False
    
    return True

def clean_dataframe_for_export(df):
    """
    Clean DataFrame by replacing NaN values with None and empty strings with None.
    This ensures consistency when saving to JSON or uploading to databases.
    
    Args:
        df: Pandas DataFrame to clean
        
    Returns:
        Cleaned DataFrame with NaN and empty strings replaced with None
    """
    # Make a copy to avoid modifying the original DataFrame
    cleaned_df = df.copy()
    
    # Replace NaN with None (which becomes null in JSON)
    cleaned_df = cleaned_df.astype(object).replace({pd.NA: None})
    cleaned_df = cleaned_df.where(pd.notnull(cleaned_df), None)
    
    # Replace empty strings with None
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == object:  # Only process string columns
            cleaned_df[col] = cleaned_df[col].replace('', None)
    
    return cleaned_df

def upload_csv_to_cosmos(csv_path, container_name, config, city=None, batch_size=50):
    """
    Upload data from a CSV file to Cosmos DB.
    
    Args:
        csv_path: Path to the CSV file
        container_name: Name of the Cosmos DB container
        config: Configuration dictionary with Cosmos DB settings
        city: Default city to use for partition key if missing (optional)
        batch_size: Number of items to upload in a single batch (optional)
        
    Returns:
        Dictionary with upload statistics
    """
    results = {
        "file": csv_path,
        "total_records": 0,
        "successful": 0,
        "failed": 0,
        "start_time": datetime.now(),
        "end_time": None,
        "errors": []
    }
    
    try:
        logger.info(f"[INFO] Loading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        results["total_records"] = len(df)
        logger.info(f"[INFO] Loaded {len(df)} records from CSV")
        
        # Clean DataFrame for export
        try:
            clean_df = clean_dataframe_for_export(df)
            logger.info(f"[INFO] DataFrame cleaned and prepared for upload")
        except Exception as e:
            logger.error(f"[ERROR] Failed to clean DataFrame: {str(e)}")
            results["errors"].append(f"DataFrame cleaning error: {str(e)}")
            results["end_time"] = datetime.now()
            return results
        
        # Initialize Cosmos DB client
        try:
            container_client = init_cosmos_client(
                config["cosmos_endpoint"], 
                config["cosmos_key"], 
                config["cosmos_db"], 
                container_name
            )
            logger.info(f"[INFO] Connected to Cosmos DB container: {container_name}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Cosmos DB: {str(e)}")
            results["errors"].append(f"Cosmos DB connection error: {str(e)}")
            results["end_time"] = datetime.now()
            return results
        
        # Convert DataFrame to records
        records = clean_df.to_dict('records')
        
        # Extract city from filename if not provided
        if not city:
            # Try to extract city from filename, example: ads_genova_rent.csv
            filename = Path(csv_path).stem  # Get filename without extension
            parts = filename.split('_')
            if len(parts) > 1:
                extracted_city = parts[1]  # Assuming format is ads_CITY_CONTRACT.csv
                city = extracted_city
                logger.info(f"[INFO] Extracted city '{city}' from filename")
            else:
                # Default fallback city
                city = "unknown"
                logger.info(f"[INFO] Using fallback city '{city}' for partition key")
        
        # Process records in batches
        batch_number = 0
        for i in range(0, len(records), batch_size):
            batch_number += 1
            batch = records[i:i+batch_size]
            logger.info(f"[INFO] Processing batch {batch_number} ({len(batch)} records)")
            
            successful_in_batch = 0
            
            for j, record in enumerate(batch):
                try:
                    # Add ID if not present
                    if 'uuid' in record and record['uuid']:
                        record['id'] = str(record['uuid'])
                    else:
                        record['id'] = str(uuid.uuid4())
                    
                    # Ensure partition key (city) is present
                    if 'city' not in record or not record['city']:
                        record['city'] = city
                    
                    # Upload to Cosmos DB
                    container_client.upsert_item(body=record)
                    successful_in_batch += 1
                    results["successful"] += 1
                except Exception as e:
                    results["failed"] += 1
                    error_message = f"Error uploading record {i+j+1}: {str(e)}"
                    logger.warning(f"[WARNING] {error_message}")
                    if len(results["errors"]) < 10:  # Limit number of stored errors
                        results["errors"].append(error_message)
            
            logger.info(f"[INFO] Batch {batch_number} complete: {successful_in_batch}/{len(batch)} records successful")
    
    except Exception as e:
        logger.error(f"[ERROR] Failed to process CSV file: {str(e)}")
        results["errors"].append(f"File processing error: {str(e)}")
    
    results["end_time"] = datetime.now()
    duration = results["end_time"] - results["start_time"]
    logger.info(f"[INFO] Upload complete: {results['successful']}/{results['total_records']} records successful")
    logger.info(f"[INFO] Duration: {duration}")
    
    return results

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Upload CSV files to Cosmos DB')
    
    # Required arguments
    parser.add_argument('csv_files', nargs='+', type=str,
                        help='Path(s) to CSV file(s) to upload')
    
    # Optional arguments
    parser.add_argument('--container', '-c', type=str, default=None,
                        help='Name of the Cosmos DB container (default: derived from filename)')
    parser.add_argument('--city', type=str, default=None,
                        help='City name to use as partition key if missing in records')
    parser.add_argument('--batch-size', '-b', type=int, default=50,
                        help='Number of records to upload in a single batch (default: 50)')
    parser.add_argument('--report', '-r', action='store_true', default=False,
                        help='Generate a detailed JSON report after upload')
    
    return parser.parse_args()

def main():
    """Main function to handle uploading CSV files to Cosmos DB."""
    args = parse_arguments()
    
    # Load environment variables
    env_vars = load_env_vars()
    
    # Build configuration
    config = {
        "cosmos_endpoint": env_vars["COSMOS_ENDPOINT"],
        "cosmos_key": env_vars["COSMOS_KEY"],
        "cosmos_db": env_vars["COSMOS_DB"]
    }
    
    # Validate configuration
    if not validate_config(config):
        sys.exit(1)
    
    # Process each CSV file
    all_results = []
    success_count = 0
    
    for csv_path in args.csv_files:
        if not os.path.exists(csv_path):
            logger.error(f"[ERROR] File not found: {csv_path}")
            continue
        
        # Determine container name if not explicitly provided
        container_name = args.container
        if not container_name:
            # Try to extract container name from filename, example: ads_genova_rent.csv
            filename = Path(csv_path).stem  # Get filename without extension
            parts = filename.split('_')
            if len(parts) > 2 and parts[0] == 'ads':
                contract_type = parts[2]  # Assuming format is ads_CITY_CONTRACT.csv
                container_name = f"ads_{contract_type}"
                logger.info(f"[INFO] Using container name '{container_name}' derived from filename")
            else:
                raise ValueError(
                    "[ERROR] Could not determine container name from filename. "
                    "Please provide a valid container name using --container option."
                )
        
        # Upload CSV file to Cosmos DB
        logger.info(f"[INFO] Processing file: {csv_path}")
        logger.info(f"[INFO] Target container: {container_name}")
        
        result = upload_csv_to_cosmos(
            csv_path=csv_path,
            container_name=container_name,
            config=config,
            city=args.city,
            batch_size=args.batch_size
        )
        
        all_results.append(result)
        if result["successful"] > 0:
            success_count += 1
    
    # Print summary
    logger.info("\n[SUMMARY]")
    logger.info(f"Total files processed: {len(args.csv_files)}")
    logger.info(f"Files with successful uploads: {success_count}")
    
    for result in all_results:
        logger.info(f"- {Path(result['file']).name}: {result['successful']}/{result['total_records']} records uploaded")
    
    # Generate detailed report if requested
    if args.report:
        report_path = f"upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_path, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            logger.info(f"[INFO] Detailed report saved to: {report_path}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to save report: {str(e)}")

if __name__ == "__main__":
    main()
