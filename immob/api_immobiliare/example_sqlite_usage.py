"""
Example script demonstrating how to use the SQLite helper functions.

This script shows how to:
1. Convert existing JSON data to a SQLite database
2. Query data from the database
3. Export filtered results to CSV
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
import argparse
from datetime import datetime

# Add parent directory to path to import helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_immobiliare.sqlite_helpers import (
    init_database, write_df_to_sqlite, read_ads_from_sqlite,
    search_ads_by_text, get_database_stats, export_to_csv
)

# Default paths
DEFAULT_DB_PATH = "data/immobili.db"
DEFAULT_JSON_PATH = "../browser_use/final_result.json"


def transform_columns(row):
    """
    Function to transform the columns of the DataFrame.
    """
    # Remove leading and trailing whitespace from all string columns
    for col in row.index:
        if isinstance(row[col], str):
            row[col] = row[col].strip()

    # Clean up text fields
    for col in ["descrizione", "titolo"]:
        if col in row and isinstance(row[col], str):
            import re
            row[col] = re.sub(r'\s+', ' ', row[col])

    # Convert numeric fields to integers
    for col in ["prezzo", "superficie", "locali", "bagni", "piano"]:
        if col in row and isinstance(row[col], str):
            try:
                import re
                match = re.search(r'([\d\.]+)', row[col])
                if match:
                    value = match.group(0)
                    value = value.replace('.', '')
                    row[col] = int(value)
            except (AttributeError, ValueError):
                # Handle the case where the regex does not find a match
                pass

    return row


def load_json_to_db(json_path, db_path, replace_existing=False):
    """
    Load JSON data to the SQLite database.
    
    Args:
        json_path: Path to the JSON file
        db_path: Path to the SQLite database
        replace_existing: Whether to replace existing records
        
    Returns:
        Tuple of (number of new records, number of updated records)
    """
    print(f"Loading data from {json_path} to {db_path}...")
    
    # Create directory for the database if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize the database
    init_database(db_path)
    
    # Load JSON data
    try:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        
        if 'immobili' in data:
            df = pd.DataFrame(data['immobili'])
        else:
            # If the JSON doesn't have an 'immobili' key, try to load it directly
            df = pd.DataFrame(data)
            
        if df.empty:
            print("No data found in the JSON file.")
            return 0, 0
            
        print(f"Loaded {len(df)} records from JSON file.")
        
        # Clean up the data
        df = df.apply(transform_columns, axis=1, result_type='expand')
        
        # Write to database
        new_records, updated_records = write_df_to_sqlite(df, db_path, replace_existing)
        
        print(f"Added {new_records} new records and updated {updated_records} existing records in the database.")
        return new_records, updated_records
        
    except Exception as e:
        print(f"Error loading JSON to database: {e}")
        return 0, 0


def query_example(db_path):
    """
    Example function demonstrating how to query the database.
    
    Args:
        db_path: Path to the SQLite database
    """
    print("\n--- Query Examples ---")
    
    # Get all records
    df_all = read_ads_from_sqlite(db_path, limit=5)
    print(f"Found {len(df_all)} total records (showing first 5):")
    if not df_all.empty:
        print(df_all[['title', 'price', 'surface', 'rooms']].head())
    
    # Filter by property type
    df_apt = read_ads_from_sqlite(
        db_path, 
        filters={'property_type': 'Appartamento | Intera proprietà'}
    )
    print(f"\nFound {len(df_apt)} apartments:")
    if not df_apt.empty:
        print(df_apt[['title', 'price', 'surface', 'rooms']].head())
    
    # Search by text
    search_term = "mare"
    df_search = search_ads_by_text(db_path, search_term)
    print(f"\nFound {len(df_search)} records containing '{search_term}':")
    if not df_search.empty:
        print(df_search[['title', 'description']].head())
    
    # Get database statistics
    stats = get_database_stats(db_path)
    if stats:
        print("\nDatabase Statistics:")
        print(f"Total Records: {stats['total_records']}")
        print(f"Latest Record Date: {stats['latest_record_date']}")
        print("Property Types:")
        for prop_type, count in stats.get('property_types', {}).items():
            print(f"  - {prop_type}: {count} records")


def export_example(db_path):
    """
    Example function demonstrating how to export filtered data to CSV.
    
    Args:
        db_path: Path to the SQLite database
    """
    print("\n--- Export Examples ---")
    
    # Export all records
    all_output_path = f"../scraping_results/immobili_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    success = export_to_csv(db_path, all_output_path)
    if success:
        print(f"Exported all records to {all_output_path}")
    
    # Export only apartments with more than 2 rooms
    apt_filters = {
        'property_type': 'Appartamento | Intera proprietà',
        'rooms': 2
    }
    apartments_output_path = f"../scraping_results/immobili_apartments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    success = export_to_csv(db_path, apartments_output_path, filters=apt_filters)
    if success:
        print(f"Exported filtered apartments to {apartments_output_path}")


def main():
    parser = argparse.ArgumentParser(description="Real Estate SQLite Database Helper Example")
    parser.add_argument("--json", default=DEFAULT_JSON_PATH, help="Path to the JSON file")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite database")
    parser.add_argument("--replace", action="store_true", help="Replace existing records")
    parser.add_argument("--query-only", action="store_true", help="Skip loading data and only run queries")
    parser.add_argument("--export", action="store_true", help="Export data to CSV files")
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(args.db), exist_ok=True)
    
    if not args.query_only:
        # Load JSON to database
        load_json_to_db(args.json, args.db, args.replace)
    
    # Run query examples
    query_example(args.db)
    
    # Export if requested
    if args.export:
        export_example(args.db)


if __name__ == "__main__":
    main()
