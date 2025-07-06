#!/usr/bin/env python3
"""
Real Estate Data Preprocessing Utilities
=======================================

Functions and transformers for preprocessing real estate data.

Author: Lucas P
Date: July 6, 2025
"""

import re
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer


# Floor normalization functions
def normalize_floor(floor_str):
    """
    Normalize floor string to numerical representation.
    
    Args:
        floor_str: String representation of floor level
        
    Returns:
        Normalized floor value as integer or float, or None if not parsable
    """
    if not floor_str or pd.isna(floor_str):
        return None
        
    floor_str = str(floor_str).lower().strip()
    
    # Floor mapping dictionary
    floor_mapping = {
        "piano terra": 0,
        "seminterrato": 0,
        "interrato (-1)": -1,
        "interrato (-2)": -2,
        "interrato (-3)": -3,
        "piano rialzato": 0.5,
        "ammezzato": 0.5,
        "su più livelli": None,  # Will be converted to np.nan
        "su due livelli": None,
        "mansarda": None
    }
    
    # Check direct mapping first
    if floor_str in floor_mapping:
        return floor_mapping[floor_str]
    
    # Try to extract numeric value
    try:
        # Handle patterns like '3° piano'
        if '°' in floor_str and 'piano' in floor_str:
            number_match = re.search(r'(\d+)°', floor_str)
            if number_match:
                return int(number_match.group(1))
        
        # Handle simple numeric values
        return int(floor_str)
    except (ValueError, TypeError):
        # Could not parse as a number
        return None


# Garage standardization functions
def standardize_garage(garage_str):
    """
    Standardize garage string to consistent categories.
    
    Args:
        garage_str: String representation of garage
        
    Returns:
        Standardized garage category as string
    """
    if not garage_str or pd.isna(garage_str):
        return None
    
    garage_str = str(garage_str).lower().strip()
    
    if 'box' in garage_str or 'box auto' in garage_str:
        return 'Box'
    elif 'posto auto' in garage_str:
        return 'Posto Auto'
    elif 'garage' in garage_str:
        return 'Garage'
    elif 'no' in garage_str or 'non presente' in garage_str or 'assente' in garage_str:
        return 'None'
    else:
        return 'Other'


def detailed_garage_standardization(garage_str):
    """
    More detailed garage standardization with sub-categories.
    
    Args:
        garage_str: String representation of garage
        
    Returns:
        Tuple of (primary_type, specific_type)
    """
    if not garage_str or pd.isna(garage_str):
        return None, None
    
    garage_str = str(garage_str).lower().strip()
    
    # Primary types
    if 'box' in garage_str or 'box auto' in garage_str:
        primary = 'Box'
    elif 'posto auto' in garage_str:
        primary = 'Posto Auto'
    elif 'garage' in garage_str:
        primary = 'Garage'
    elif 'no' in garage_str or 'non presente' in garage_str or 'assente' in garage_str:
        return 'None', 'None'
    else:
        return 'Other', 'Other'
    
    # Specific types
    if 'doppio' in garage_str:
        specific = f"{primary} Doppio"
    elif 'singolo' in garage_str:
        specific = f"{primary} Singolo"
    elif 'coperto' in garage_str:
        specific = f"{primary} Coperto"
    elif 'scoperto' in garage_str:
        specific = f"{primary} Scoperto"
    else:
        specific = primary
        
    return primary, specific


# Feature extraction functions
def has_feature(features_str, feature):
    """
    Check if a specific feature is mentioned in the features string.
    
    Args:
        features_str: String representation of features (comma-separated)
        feature: Feature to check for
        
    Returns:
        Boolean indicating if feature is present
    """
    if not features_str or pd.isna(features_str):
        return False
    
    features_str = str(features_str).lower().strip()
    feature = str(feature).lower().strip()
    
    # Split features and check if target feature is present
    features_list = [f.strip() for f in features_str.split(',')]
    return feature in features_list


# Custom transformers
class NumericExtractor(BaseEstimator, TransformerMixin):
    """Transform 'surface' column to ensure numeric values."""
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        X_copy = X.copy()
        X_copy['surface'] = pd.to_numeric(X_copy['surface'], errors='coerce')
        return X_copy


class FloorNormalizer(BaseEstimator, TransformerMixin):
    """Transform 'floor' column to normalized numeric values."""
    
    def __init__(self):
        self.floor_mapping = {
            "piano terra": 0,
            "seminterrato": 0,
            "interrato (-1)": -1,
            "interrato (-2)": -2,
            "interrato (-3)": -3,
            "piano rialzato": 0.5,
            "ammezzato": 0.5,
            "su più livelli": None
        }
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        X_copy = X.copy()
        X_copy['floor_normalized'] = X_copy['floor'].apply(self._normalize_floor)
        return X_copy
    
    def _normalize_floor(self, floor_str):
        return normalize_floor(floor_str)


# Preprocessing pipeline creation
def create_preprocessing_pipeline(df=None):
    """
    Create a preprocessing pipeline for real estate data.
    
    Args:
        df: Optional DataFrame to fit encoders
        
    Returns:
        Tuple of (preprocessing_pipeline, column_info) where column_info contains
        metadata about columns used in the pipeline
    """
    # Define column groupings
    column_info = {
        'numeric': ['surface', 'rooms', 'bathrooms', 'floor_normalized'],
        'categorical': ['city', 'zone', 'property_type', 'condition', 'heating'],
        'binary': ['elevator', 'balcony', 'terrace', 'garden', 'parking', 'air_conditioning']
    }
    
    # Numeric preprocessing
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Categorical preprocessing
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse=False))
    ])
    
    # Binary preprocessing
    binary_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value=False))
    ])
    
    # Combine preprocessing steps
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, column_info['numeric']),
            ('cat', categorical_transformer, column_info['categorical']),
            ('bin', binary_transformer, column_info['binary'])
        ]
    )
    
    # Fit preprocessor if DataFrame is provided
    if df is not None:
        preprocessor.fit(df)
    
    return preprocessor, column_info


# Feature extraction and engineering functions
def extract_feature_columns(df, feature_names, min_occurrences=100):
    """
    Extract binary feature columns from comma-separated feature string.
    
    Args:
        df: DataFrame with a 'features' column
        feature_names: List of feature names to extract
        min_occurrences: Minimum number of occurrences required to keep a feature
        
    Returns:
        DataFrame with additional binary feature columns
    """
    result_df = df.copy()
    
    # Create binary columns for each feature
    for feature in feature_names:
        col_name = f"has_{feature.lower().replace(' ', '_')}"
        result_df[col_name] = result_df['features'].apply(
            lambda x: has_feature(x, feature)
        )
        
    # Filter columns by minimum occurrences
    feature_cols = [col for col in result_df.columns if col.startswith('has_')]
    kept_cols = []
    
    for col in feature_cols:
        if result_df[col].sum() >= min_occurrences:
            kept_cols.append(col)
        else:
            result_df.drop(col, axis=1, inplace=True)
            
    print(f"Extracted {len(kept_cols)} binary feature columns")
    return result_df


def engineer_price_per_sqm(df):
    """
    Calculate price per square meter.
    
    Args:
        df: DataFrame with 'price' and 'surface' columns
        
    Returns:
        DataFrame with added 'price_per_sqm' column
    """
    result_df = df.copy()
    
    # Calculate price per square meter
    mask = (result_df['price'].notna() & 
            result_df['surface'].notna() & 
            (result_df['surface'] > 0))
    
    result_df.loc[mask, 'price_per_sqm'] = (
        result_df.loc[mask, 'price'] / result_df.loc[mask, 'surface']
    )
    
    return result_df
