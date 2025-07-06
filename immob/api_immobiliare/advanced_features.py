#!/usr/bin/env python3
"""
Advanced Feature Engineering for Real Estate Data
===============================================

This module provides advanced feature engineering capabilities for real estate data,
including text extraction from descriptions, geographic features, and time-based features.

Author: Lucas P
Date: July 6, 2025
"""

import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union, Optional
from datetime import datetime
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# Feature extraction patterns
FEATURE_PATTERNS = {
    # Location quality indicators
    'location_features': {
        'near_center': r'\b(centro|central|vicino\s+al\s+centro|in\s+centro)\b',
        'sea_view': r'\b(vista\s+mare|fronte\s+mare|sul\s+mare|affaccia\s+sul\s+mare)\b',
        'near_park': r'\b(parco|giardini|verde|area\s+verde)\b',
        'near_transport': r'\b(metro|bus|tram|stazione|mezzi\s+pubblici|trasporti)\b',
        'near_services': r'\b(servizi|negozi|scuole|ospedale|supermercato|centro\s+commerciale)\b'
    },
    
    # Property quality indicators
    'property_features': {
        'renovated': r'\b(ristrutturato|ristrutturazione|recentemente\s+ristrutturato)\b',
        'modern': r'\b(moderno|contemporaneo|di\s+design|recente\s+costruzione)\b',
        'luxury': r'\b(lusso|pregio|prestigio|elegante|signorile|alto\s+standing)\b',
        'panoramic': r'\b(panoramico|panorama|vista\s+panoramica|vista\s+aperta)\b',
        'bright': r'\b(luminoso|soleggiato|luce|esposizione|sud|sud-est|sud-ovest)\b'
    },
    
    # Amenities
    'amenity_features': {
        'terrace': r'\b(terrazzo|terrazza|terrazzi)\b',
        'garden': r'\b(giardino|area\s+verde\s+privata)\b',
        'parking': r'\b(posto\s+auto|box|garage|parcheggio)\b',
        'elevator': r'\b(ascensore|lift|elevatore)\b',
        'air_conditioning': r'\b(aria\s+condizionata|climatizzatore|climatizzato)\b',
        'heating': r'\b(riscaldamento\s+autonomo|riscaldamento\s+centralizzato)\b',
        'security': r'\b(portineria|custode|sorveglianza|vigilanza)\b'
    }
}


class DescriptionFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Extract features from property descriptions using regex patterns.
    
    This transformer extracts binary features from text descriptions based on
    predefined regex patterns for various property attributes.
    """
    
    def __init__(self, feature_patterns: Dict[str, Dict[str, str]] = None):
        """
        Initialize with feature patterns.
        
        Args:
            feature_patterns: Dictionary of feature category to pattern mapping
        """
        self.feature_patterns = feature_patterns or FEATURE_PATTERNS
        # Flatten the nested dictionary to get all feature names
        self.feature_names = [
            f"{category}_{feature}" 
            for category, patterns in self.feature_patterns.items() 
            for feature in patterns.keys()
        ]
    
    def fit(self, X, y=None):
        """Fit method (no-op for this transformer)."""
        return self
    
    def transform(self, X):
        """
        Transform text descriptions into binary features.
        
        Args:
            X: DataFrame or Series containing description text
            
        Returns:
            DataFrame with binary features
        """
        # Handle different input types
        if isinstance(X, pd.DataFrame):
            if 'description' in X.columns:
                descriptions = X['description'].fillna('')
            else:
                # Use the first text column we can find
                text_cols = X.select_dtypes(include=['object']).columns
                if len(text_cols) > 0:
                    descriptions = X[text_cols[0]].fillna('')
                else:
                    raise ValueError("No text column found in DataFrame")
        elif isinstance(X, pd.Series):
            descriptions = X.fillna('')
        else:
            raise ValueError("Input must be a pandas DataFrame or Series")
        
        # Create an output dataframe with binary features
        result = pd.DataFrame(index=X.index)
        
        # Extract features using regex patterns
        for category, patterns in self.feature_patterns.items():
            for feature_name, pattern in patterns.items():
                col_name = f"{category}_{feature_name}"
                result[col_name] = descriptions.str.contains(
                    pattern, 
                    case=False, 
                    regex=True
                ).astype(int)
        
        return result
    
    def get_feature_names_out(self):
        """Return feature names for the transformer output."""
        return self.feature_names


class GeographicFeatureTransformer(BaseEstimator, TransformerMixin):
    """
    Transform geographic coordinates into useful features.
    
    This transformer generates features from latitude and longitude, including:
    - Distance to city center
    - Distance to nearest major landmark
    - Distances to amenities (when available)
    """
    
    def __init__(self, city_centers: Dict[str, tuple] = None, landmarks: Dict[str, Dict[str, tuple]] = None):
        """
        Initialize with geographic reference points.
        
        Args:
            city_centers: Dictionary mapping city names to (lat, lon) coordinates
            landmarks: Dictionary mapping city names to landmark dictionaries
        """
        # Default city centers (latitude, longitude) for major Italian cities
        self.city_centers = city_centers or {
            'genova': (44.4056, 8.9463),
            'milano': (45.4642, 9.1900),
            'roma': (41.9028, 12.4964),
            'torino': (45.0703, 7.6869),
            'napoli': (40.8518, 14.2681),
            'firenze': (43.7696, 11.2558)
        }
        
        # Default landmarks by city
        self.landmarks = landmarks or {}
    
    def fit(self, X, y=None):
        """Fit method (no-op for this transformer)."""
        return self
    
    def transform(self, X):
        """
        Transform geographic coordinates into distance features.
        
        Args:
            X: DataFrame containing latitude and longitude columns
            
        Returns:
            DataFrame with distance-based features
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Check if latitude and longitude columns are available
        if 'latitude' not in X.columns or 'longitude' not in X.columns:
            raise ValueError("DataFrame must contain 'latitude' and 'longitude' columns")
        
        # Fill missing values with median
        lat_median = X['latitude'].median()
        lon_median = X['longitude'].median()
        
        latitude = X['latitude'].fillna(lat_median)
        longitude = X['longitude'].fillna(lon_median)
        
        # Create an output dataframe
        result = pd.DataFrame(index=X.index)
        
        # Get city information if available
        city_col = None
        for col in ['city', 'città', 'comune']:
            if col in X.columns:
                city_col = col
                break
        
        # Calculate distance to city center
        if city_col and city_col in X.columns:
            # For each city in the dataset, calculate distance to its center
            for city, (center_lat, center_lon) in self.city_centers.items():
                # Create a mask for this city
                city_mask = X[city_col].str.lower() == city.lower()
                
                if city_mask.sum() > 0:
                    # Calculate distances only for rows matching this city
                    distances = self._haversine_distance(
                        latitude[city_mask], 
                        longitude[city_mask],
                        center_lat, 
                        center_lon
                    )
                    
                    # Initialize the column if it doesn't exist
                    if 'distance_to_center' not in result.columns:
                        result['distance_to_center'] = float('nan')
                        
                    # Update distances for this city
                    result.loc[city_mask, 'distance_to_center'] = distances
        else:
            # If no city information, use the first city center as default
            default_city = list(self.city_centers.keys())[0]
            center_lat, center_lon = self.city_centers[default_city]
            
            result['distance_to_center'] = self._haversine_distance(
                latitude, longitude, center_lat, center_lon
            )
        
        return result
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the Haversine distance between points.
        
        Args:
            lat1, lon1: First point coordinates (can be Series)
            lat2, lon2: Second point coordinates (single point)
            
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Radius of Earth in kilometers
        
        return c * r


class TimeFeatureTransformer(BaseEstimator, TransformerMixin):
    """
    Transform dates and timestamps into useful time-based features.
    
    This transformer extracts time-based features like:
    - Days since listing
    - Season (Spring, Summer, Fall, Winter)
    - Month of year
    - Day of week
    - Holiday proximity
    """
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Initialize with reference date.
        
        Args:
            reference_date: Date to use for "days since" calculations
        """
        self.reference_date = reference_date or datetime.now()
    
    def fit(self, X, y=None):
        """Fit method (no-op for this transformer)."""
        return self
    
    def transform(self, X):
        """
        Transform date columns into time-based features.
        
        Args:
            X: DataFrame containing date columns
            
        Returns:
            DataFrame with time-based features
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Find date columns in the DataFrame
        date_cols = []
        for col in X.columns:
            if X[col].dtype == 'datetime64[ns]' or 'date' in col.lower() or 'time' in col.lower():
                try:
                    # Try to convert to datetime
                    X[col] = pd.to_datetime(X[col], errors='coerce')
                    if not X[col].isna().all():  # Only include if there are valid dates
                        date_cols.append(col)
                except:
                    continue
        
        if not date_cols:
            # No valid date columns found
            return pd.DataFrame(index=X.index)
        
        # Create an output dataframe
        result = pd.DataFrame(index=X.index)
        
        # Process each date column
        for date_col in date_cols:
            dates = X[date_col]
            prefix = date_col.lower().replace('date', '').replace('time', '').strip('_')
            if not prefix:
                prefix = date_col
            
            # Add days since reference date
            days_diff = (self.reference_date - dates).dt.days
            result[f'{prefix}_days_since'] = days_diff
            
            # Add month of year (1-12)
            result[f'{prefix}_month'] = dates.dt.month
            
            # Add day of week (0-6, 0=Monday)
            result[f'{prefix}_day_of_week'] = dates.dt.dayofweek
            
            # Add season (1=Spring, 2=Summer, 3=Fall, 4=Winter)
            month = dates.dt.month
            season = (
                (month % 12 + 3) // 3
            ).replace({1: 'Winter', 2: 'Spring', 3: 'Summer', 4: 'Fall'})
            result[f'{prefix}_season'] = season
            
            # Add quarter (1-4)
            result[f'{prefix}_quarter'] = dates.dt.quarter
            
            # Add week of year (1-53)
            result[f'{prefix}_week'] = dates.dt.isocalendar().week
            
            # Add binary indicator for weekend
            result[f'{prefix}_is_weekend'] = (dates.dt.dayofweek >= 5).astype(int)
        
        return result


class TextVectorizerTransformer(BaseEstimator, TransformerMixin):
    """
    Transform property descriptions into vector representations.
    
    This transformer uses NLP techniques to convert property descriptions
    into numerical features using either count-based or TF-IDF vectorization.
    """
    
    def __init__(self, 
                 vectorizer_type: str = 'tfidf', 
                 max_features: int = 100,
                 ngram_range: tuple = (1, 2),
                 stop_words: str = 'italian'):
        """
        Initialize with vectorization parameters.
        
        Args:
            vectorizer_type: Type of vectorizer ('count' or 'tfidf')
            max_features: Maximum number of features to extract
            ngram_range: Range of n-grams to consider
            stop_words: Language for stop words removal
        """
        self.vectorizer_type = vectorizer_type
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.stop_words = stop_words
        
        # Initialize the appropriate vectorizer
        if vectorizer_type.lower() == 'count':
            self.vectorizer = CountVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                stop_words=stop_words
            )
        else:  # Default to TF-IDF
            self.vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                stop_words=stop_words
            )
    
    def fit(self, X, y=None):
        """
        Fit the vectorizer on property descriptions.
        
        Args:
            X: DataFrame or Series containing descriptions
            y: Target variable (not used)
            
        Returns:
            Self
        """
        # Extract text column
        if isinstance(X, pd.DataFrame):
            if 'description' in X.columns:
                text = X['description'].fillna('')
            else:
                # Use the first text column we can find
                text_cols = X.select_dtypes(include=['object']).columns
                if len(text_cols) > 0:
                    text = X[text_cols[0]].fillna('')
                else:
                    raise ValueError("No text column found in DataFrame")
        elif isinstance(X, pd.Series):
            text = X.fillna('')
        else:
            raise ValueError("Input must be a pandas DataFrame or Series")
        
        # Fit the vectorizer
        self.vectorizer.fit(text)
        return self
    
    def transform(self, X):
        """
        Transform descriptions into vector representations.
        
        Args:
            X: DataFrame or Series containing descriptions
            
        Returns:
            Sparse matrix of vectorized text
        """
        # Extract text column
        if isinstance(X, pd.DataFrame):
            if 'description' in X.columns:
                text = X['description'].fillna('')
            else:
                # Use the first text column we can find
                text_cols = X.select_dtypes(include=['object']).columns
                if len(text_cols) > 0:
                    text = X[text_cols[0]].fillna('')
                else:
                    raise ValueError("No text column found in DataFrame")
        elif isinstance(X, pd.Series):
            text = X.fillna('')
        else:
            raise ValueError("Input must be a pandas DataFrame or Series")
        
        # Transform the text to vectors
        vectors = self.vectorizer.transform(text)
        
        # Convert to DataFrame with feature names
        feature_names = [f"text_{name}" for name in self.vectorizer.get_feature_names_out()]
        result = pd.DataFrame(
            vectors.toarray(),
            index=X.index,
            columns=feature_names
        )
        
        return result
    
    def get_feature_names_out(self):
        """Return feature names for the transformer output."""
        return [f"text_{name}" for name in self.vectorizer.get_feature_names_out()]


def create_advanced_feature_pipeline(text_max_features=50, include_geographic=True, include_time=True):
    """
    Create a comprehensive pipeline for advanced feature engineering.
    
    This function creates a pipeline that combines multiple feature engineering
    transformers for comprehensive feature extraction.
    
    Args:
        text_max_features: Maximum number of text features to extract
        include_geographic: Whether to include geographic features
        include_time: Whether to include time-based features
        
    Returns:
        A scikit-learn Pipeline for feature engineering
    """
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.impute import SimpleImputer
    
    # Define transformers
    transformers = []
    
    # Basic feature extraction from description
    transformers.append(
        ('description_features', DescriptionFeatureExtractor(), ['description'])
    )
    
    # Text vectorization
    transformers.append(
        ('text_vectorizer', TextVectorizerTransformer(max_features=text_max_features), ['description'])
    )
    
    # Geographic features
    if include_geographic:
        transformers.append(
            ('geographic_features', GeographicFeatureTransformer(), ['latitude', 'longitude', 'city'])
        )
    
    # Time features
    if include_time:
        transformers.append(
            ('time_features', TimeFeatureTransformer(), ['date_posted', 'date_updated'])
        )
    
    # Create the pipeline
    pipeline = ColumnTransformer(
        transformers=transformers,
        remainder='passthrough'
    )
    
    # Add final preprocessing steps
    full_pipeline = Pipeline([
        ('feature_engineering', pipeline),
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    return full_pipeline
