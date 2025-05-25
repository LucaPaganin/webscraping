"""
Example script demonstrating data type conversion for real estate ads.

This script shows how to:
1. Load a CSV file with real estate data
2. Convert column data types appropriately
3. Write cleaned data to a SQLite database
4. Read and analyze the data
"""

import pandas as pd
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path to import helpers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlite_helpers import (
    init_database, write_df_to_sqlite, read_ads_from_sqlite,
    clean_df_from_sqlite, get_database_stats
)

def process_real_estate_data(csv_path, db_path):
    """
    Process real estate data from CSV, convert types, and save to SQLite.
    
    Args:
        csv_path: Path to the CSV file with real estate data
        db_path: Path to the SQLite database to create/update
    """
    print(f"\n--- Processing Real Estate Data ---")
    print(f"Loading data from {csv_path}...")
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from CSV.")
    
    # Print columns and their current data types
    print("\nOriginal column types:")
    print(df.dtypes)
    
    # Print some sample data
    print("\nSample data:")
    print(df.head(2))
    
    # Create directory for the database if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize the database
    init_database(db_path)
    
    # Write to database (the transform_df_dtypes function is called inside)
    new_records, updated_records = write_df_to_sqlite(df, db_path, replace_existing=True)
    print(f"\nAdded {new_records} new records and updated {updated_records} existing records in the database.")
    
    return df


def analyze_real_estate_data(db_path):
    """
    Analyze real estate data from the SQLite database.
    
    Args:
        db_path: Path to the SQLite database
    """
    print("\n--- Analyzing Real Estate Data ---")
    
    # Read data from SQLite (with automatic cleaning)
    df = read_ads_from_sqlite(db_path)
    print(f"Retrieved {len(df)} records from database.")
    
    # Print columns and their transformed data types
    print("\nProcessed column types:")
    print(df.dtypes)
    
    # Get database statistics
    stats = get_database_stats(db_path)
    if stats:
        print("\nDatabase Statistics:")
        print(f"Total Records: {stats['total_records']}")
        
        if stats.get('property_types'):
            print("\nProperty Types:")
            for prop_type, count in stats.get('property_types', {}).items():
                print(f"  - {prop_type}: {count} records")
        
        if stats.get('top_cities'):
            print("\nTop Cities:")
            for city, count in stats.get('top_cities', {}).items():
                if city and city.lower() != 'null':
                    print(f"  - {city}: {count} records")
    
    # Basic data analysis
    if 'surface_m2' in df.columns and len(df) > 0:
        # Calculate price per square meter for properties with both price and surface data
        if 'price' in df.columns:
            # Extract numeric values from price strings
            df['price_numeric'] = df['price'].str.extract(r'(\d+(?:\.\d+)?)')
            df['price_numeric'] = pd.to_numeric(df['price_numeric'], errors='coerce')
            
            # Calculate price per square meter
            valid_df = df[df['surface_m2'].notna() & df['price_numeric'].notna()]
            if len(valid_df) > 0:
                valid_df['price_per_m2'] = valid_df['price_numeric'] / valid_df['surface_m2']
                
                print("\nPrice per square meter statistics:")
                print(f"Average: {valid_df['price_per_m2'].mean():.2f} €/m²")
                print(f"Median: {valid_df['price_per_m2'].median():.2f} €/m²")
                print(f"Min: {valid_df['price_per_m2'].min():.2f} €/m²")
                print(f"Max: {valid_df['price_per_m2'].max():.2f} €/m²")
        
        # Surface statistics
        print("\nSurface statistics:")
        print(f"Average: {df['surface_m2'].mean():.2f} m²")
        print(f"Median: {df['surface_m2'].median():.2f} m²")
        print(f"Min: {df['surface_m2'].min():.2f} m²")
        print(f"Max: {df['surface_m2'].max():.2f} m²")
    
    # Room distribution
    if 'rooms' in df.columns and len(df) > 0:
        room_counts = df['rooms'].value_counts().sort_index()
        print("\nRoom distribution:")
        for rooms, count in room_counts.items():
            if not pd.isna(rooms):
                print(f"  - {rooms} rooms: {count} properties")
    
    return df


def main():
    # Define file paths
    csv_path = "../browser_use/immobili.csv"  # Update this path if needed
    db_path = "data/immobili.db"
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
        csv_path = input("Please enter the path to the CSV file: ")
        if not os.path.exists(csv_path):
            print(f"CSV file not found at {csv_path}")
            sys.exit(1)
    
    # Process data
    df_original = process_real_estate_data(csv_path, db_path)
    
    # Analyze data
    df_processed = analyze_real_estate_data(db_path)


if __name__ == "__main__":
    main()
