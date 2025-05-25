"""
Example script demonstrating how to convert real estate ads DataFrame columns to the correct data types.

This script shows how to:
1. Create a sample DataFrame
2. Convert column data types appropriately
3. Analyze the DataFrame

Usage:
    python data_type_conversion_example.py
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path to import helpers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlite_helpers import transform_df_dtypes, clean_df_from_sqlite

def create_sample_dataframe():
    """
    Create a sample DataFrame with mixed data types.
    """
    # Sample data with mixed types
    data = {
        "id": [1, 2, "3", None, 5],
        "uuid": ["abc123", "def456", "ghi789", "jkl012", "mno345"],
        "title": ["Appartamento in centro", "Villa con piscina", "  Monolocale vista mare  ", "Attico di lusso", "Bilocale ristrutturato"],
        "url": ["https://example.com/1", "https://example.com/2", "https://example.com/3", "https://example.com/4", "https://example.com/5"],
        "geoHash": ["u0m1p", "u0m2q", "u0m3r", "u0m4s", "u0m5t"],
        "type": ["sell", "rent", "sell", "sell", "rent"],
        "typology_id": [1, 2, "3", 4, "5"],
        "typology_name": ["Appartamento", "Villa", "Monolocale", "Attico", "Bilocale"],
        "contract": ["vendita", "affitto", "vendita", "vendita", "affitto"],
        "isNew": ["True", "False", "True", "Sì", "No"],
        "luxury": [1, 0, "true", "false", None],
        "visibility": ["S", "N", "S", "N", "S"],
        "price_value": [250000, "320000", 95000, "680000", 125000],
        "price_formatted": ["€ 250.000", "€ 320.000", "€ 95.000", "€ 680.000", "€ 125.000"],
        "price_min": [240000, 310000, 90000, 670000, 120000],
        "surface": ["80 m²", "150 m²", "35 m²", "120 m²", "55 m²"],
        "rooms": [3, 5, 1, 4, 2],
        "bathrooms": ["2", 3, "1", 2, "1"],
        "floor": ["2° piano", "Piano terra con giardino", "5° piano", "ultimo piano", "1° piano"],
        "floor_number": ["2", "piano terra", "5", "6", "1"],
        "elevator": ["sì", "no", "Sì", "No", "S"],
        "latitude": ["44.4056", 44.4078, "44.4112", 44.4098, "44.4033"],
        "longitude": ["8.9463", "8.9425", 8.9471, "8.9491", 8.9452],
        "city": ["Genova", "Genova", "Genova", "Genova", "Genova"],
        "province": ["GE", "GE", "GE", "GE", "GE"],
        "description": ["Bellissimo appartamento...", "Villa con ampio giardino...", "  Monolocale a pochi passi dal mare  ", "Attico panoramico...", "Bilocale recentemente ristrutturato..."],
        "agency_id": [101, "102", 103, "104", 105],
        "photo_url_medium": ["https://img.example.com/1_med.jpg", "https://img.example.com/2_med.jpg", "https://img.example.com/3_med.jpg", "https://img.example.com/4_med.jpg", "https://img.example.com/5_med.jpg"]
    }
    
    return pd.DataFrame(data)

def main():
    # Create sample DataFrame
    df = create_sample_dataframe()
    
    print("=== Original DataFrame ===")
    print(df.head(2))
    print("\nOriginal data types:")
    print(df.dtypes)
    
    # Transform DataFrame data types
    df_transformed = transform_df_dtypes(df)
    
    print("\n=== Transformed DataFrame ===")
    print(df_transformed.head(2))
    print("\nTransformed data types:")
    print(df_transformed.dtypes)
    
    # Check specific transformations
    print("\n=== Type Conversion Examples ===")
    
    # Integer columns
    print("\nInteger columns (original vs transformed):")
    for col in ['id', 'typology_id', 'rooms', 'bathrooms']:
        if col in df.columns:
            print(f"{col}:")
            print(f"  Original: {df[col].tolist()}")
            print(f"  Transformed: {df_transformed[col].tolist()}")
    
    # Boolean columns
    print("\nBoolean columns (original vs transformed):")
    for col in ['isNew', 'luxury', 'visibility', 'elevator']:
        if col in df.columns:
            print(f"{col}:")
            print(f"  Original: {df[col].tolist()}")
            print(f"  Transformed: {df_transformed[col].tolist()}")
    
    # Special transformations
    print("\nSpecial transformations:")
    
    # Surface to surface_m2
    if 'surface' in df.columns and 'surface_m2' in df_transformed.columns:
        print("Surface extraction:")
        for i in range(len(df)):
            print(f"  {df['surface'].iloc[i]} -> {df_transformed['surface_m2'].iloc[i]}")
    
    # Floor number normalization
    if 'floor_number' in df.columns:
        print("\nFloor number normalization:")
        for i in range(len(df)):
            print(f"  {df['floor_number'].iloc[i]} -> {df_transformed['floor_number'].iloc[i]}")
    
    # Cleaned text
    if 'description' in df.columns:
        print("\nText cleaning example (description):")
        for i in range(2, 3):  # Just show one example with visible whitespace
            print(f"  Original: '{df['description'].iloc[i]}'")
            print(f"  Cleaned: '{df_transformed['description'].iloc[i]}'")

if __name__ == "__main__":
    main()
