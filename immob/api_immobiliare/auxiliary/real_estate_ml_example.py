#!/usr/bin/env python3
"""
Real Estate ML Example
=====================

Example script demonstrating how to use preprocessing and ML utilities
with real estate data.

Author: Lucas P
Date: July 6, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Import our modular components
from preprocessing import normalize_floor, standardize_garage, extract_feature_columns, engineer_price_per_sqm
from preprocessing import create_preprocessing_pipeline
from ml_utils import train_multiple_models, select_features, train_model_with_selected_features


def main():
    """Main function demonstrating the workflow."""
    # Load data - adjust the path as needed
    data_path = Path(__file__).parent.parent / 'data' / 'genova_sale_20250706_120433.csv'
    
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        print("Please run fetch_ads_cli.py first to collect some data")
        return
        
    print(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Basic preprocessing
    print(f"Raw data shape: {df.shape}")
    print(f"Columns: {', '.join(df.columns)}")
    
    # Apply preprocessing functions
    print("\nApplying preprocessing steps...")
    df['floor_normalized'] = df['floor'].apply(normalize_floor)
    df['garage_type'] = df['garage'].apply(standardize_garage)
    
    # Extract feature columns
    print("\nExtracting binary feature columns...")
    if 'features' in df.columns:
        # Get unique features
        all_features = []
        df['features'].dropna().apply(
            lambda x: all_features.extend([f.strip() for f in str(x).split(',')])
        )
        unique_features = list(set(all_features))
        
        # Extract binary feature columns
        df = extract_feature_columns(df, unique_features, min_occurrences=10)
    
    # Engineer price per square meter
    df = engineer_price_per_sqm(df)
    
    print(f"\nProcessed data shape: {df.shape}")
    
    # Display basic statistics
    print("\nBasic statistics for key columns:")
    numeric_cols = ['price', 'surface', 'rooms', 'price_per_sqm', 'floor_normalized']
    print(df[numeric_cols].describe())
    
    # Machine learning preparation
    print("\nPreparing machine learning pipeline...")
    
    # Select only relevant columns
    y = df['price'].copy()
    X = df.drop(['price', 'price_formatted', 'price_per_sqm', 'id', 'source_url', 'source_website'], 
               axis=1, errors='ignore')
    
    # Create preprocessing pipeline
    print("\nCreating preprocessing pipeline...")
    preprocessor, column_info = create_preprocessing_pipeline(df)
    
    # Split data (this is handled inside the ML functions but shown here for clarity)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train and evaluate models
    print("\nTraining and evaluating multiple models...")
    print("(This might take a few minutes)")
    try:
        results = train_multiple_models(X_train, X_test, y_train, y_test, preprocessor)
        
        # Train model with selected features
        print("\n\nTraining model with selected features...")
        train_model_with_selected_features(
            X, y, model_type='random_forest', n_features=20, 
            selection_method='f_regression', test_size=0.2, random_state=42
        )
    except Exception as e:
        print(f"\nError during model training: {e}")
        print("This is likely due to missing or improperly formatted data.")
        print("Please check your dataset and preprocessing steps.")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
