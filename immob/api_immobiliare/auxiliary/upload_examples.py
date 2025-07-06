#!/usr/bin/env python3
"""
Real Estate Data Upload - Example Usage
=======================================

Examples of how to use the upload_data.py tool programmatically.

Author: Lucas P
Date: July 6, 2025
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path if running from examples folder
parent_dir = Path(__file__).parent.parent
if parent_dir not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import our modules
from data_manager import RealEstateDataManager
from retrievers import RealEstateAdRetriever
from config import load_configuration
from upload_data import load_csv_to_ads, upload_csv_with_batches


def example_sqlite_upload():
    """Example of uploading data to SQLite database."""
    print("\n--- Example: Upload to SQLite ---")
    
    # Configuration
    config = load_configuration()
    retriever = RealEstateAdRetriever.create_mock_retriever(config)
    data_manager = RealEstateDataManager(retriever, config)
    
    # Find CSV files in data directory
    data_dir = Path("data")
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in data directory")
        return
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Upload each file to SQLite
    for csv_path in csv_files:
        print(f"\nProcessing: {csv_path}")
        
        # Upload with batch processing
        result = upload_csv_with_batches(
            csv_path=csv_path,
            data_manager=data_manager,
            output_format='sqlite',
            batch_size=50,
            db_path="real_estate.db",
            table_name="ads"
        )
        
        # Print results
        print(f"Upload complete: {result['successful']}/{result['total_records']} records successful")
        if result['errors']:
            print(f"Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:  # Show only first 3 errors
                print(f"- {error}")


def example_cosmos_upload():
    """Example of uploading data to Cosmos DB."""
    print("\n--- Example: Upload to Cosmos DB ---")
    
    # Check if environment variables are set
    cosmos_endpoint = os.environ.get("COSMOS_DB_ACCOUNT_URI")
    cosmos_key = os.environ.get("COSMOS_DB_ACCOUNT_KEY")
    cosmos_db = os.environ.get("COSMOS_DB_DATABASE_NAME")
    
    if not all([cosmos_endpoint, cosmos_key, cosmos_db]):
        print("Cosmos DB environment variables not set, skipping example")
        return
    
    # Configuration
    config = load_configuration()
    retriever = RealEstateAdRetriever.create_mock_retriever(config)
    data_manager = RealEstateDataManager(retriever, config)
    
    # Find CSV files in data directory
    data_dir = Path("data")
    csv_files = list(data_dir.glob("*_rent.csv"))  # Get only rental ads
    
    if not csv_files:
        print("No CSV files found matching the pattern")
        return
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Upload each file to Cosmos DB
    for csv_path in csv_files:
        print(f"\nProcessing: {csv_path}")
        
        # Extract city from filename (assuming naming pattern: city_rent.csv)
        city = csv_path.stem.split('_')[0]
        container_name = f"{city}_rentals"
        
        # Upload with batch processing
        result = upload_csv_with_batches(
            csv_path=csv_path,
            data_manager=data_manager,
            output_format='cosmos',
            batch_size=20,  # Smaller batches for Cosmos DB
            container_name=container_name,
            city=city
        )
        
        # Print results
        print(f"Upload complete: {result['successful']}/{result['total_records']} records successful")


def example_transform_and_save():
    """Example of loading, transforming, and saving data."""
    print("\n--- Example: Transform and Save ---")
    
    # Configuration
    config = load_configuration()
    retriever = RealEstateAdRetriever.create_mock_retriever(config)
    data_manager = RealEstateDataManager(retriever, config)
    
    # Find a CSV file to process
    csv_path = next(Path("data").glob("*.csv"), None)
    
    if not csv_path:
        print("No CSV file found in data directory")
        return
    
    print(f"Processing: {csv_path}")
    
    # Load ads from CSV
    ads = load_csv_to_ads(csv_path)
    print(f"Loaded {len(ads)} ads from CSV")
    
    if not ads:
        print("No valid ads found in the CSV file")
        return
    
    # Apply a simple transformation (e.g., filter by price)
    min_price = 100000
    filtered_ads = [ad for ad in ads if ad.price and ad.price >= min_price]
    print(f"Filtered to {len(filtered_ads)} ads with price >= {min_price}")
    
    # Save the filtered results
    output_filename = f"filtered_{csv_path.stem}.json"
    success = data_manager.save_to_json(filtered_ads, output_filename)
    
    if success:
        print(f"Successfully saved filtered data to {output_filename}")
    else:
        print("Failed to save filtered data")


if __name__ == "__main__":
    print("Real Estate Data Upload - Example Usage")
    print("=====================================")
    
    example_sqlite_upload()
    example_cosmos_upload()
    example_transform_and_save()
    
    print("\nAll examples complete")
