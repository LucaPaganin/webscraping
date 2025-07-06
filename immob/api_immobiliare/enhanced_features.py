#!/usr/bin/env python3
"""
Enhanced Feature Engineering for Real Estate Data
===============================================

This module extends the advanced_features.py module with additional feature engineering
capabilities, including price trend analysis, neighborhood clustering, sentiment analysis,
energy efficiency features, and integration with external data sources.

Author: Lucas P
Date: July 6, 2025
"""

import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union, Optional, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Import existing advanced features
from advanced_features import (
    DescriptionFeatureExtractor,
    GeographicFeatureTransformer,
    TimeFeatureTransformer,
    TextVectorizerTransformer
)

# Setup logging
logger = logging.getLogger(__name__)


class PriceTrendAnalyzer(BaseEstimator, TransformerMixin):
    """
    Analyze price trends and extract relevant features.
    
    This transformer analyzes price history data to extract trends,
    price changes, and volatility metrics for real estate properties.
    """
    
    def __init__(self, window_sizes: List[int] = None, reference_date: Optional[datetime] = None):
        """
        Initialize the price trend analyzer.
        
        Args:
            window_sizes: List of window sizes (in days) for trend analysis
            reference_date: Reference date for trend calculations
        """
        self.window_sizes = window_sizes or [7, 30, 90, 180]
        self.reference_date = reference_date or datetime.now()
        self.price_history = {}
        self.market_trends = {}
    
    def fit(self, X, y=None):
        """
        Fit the analyzer by calculating market-level trends.
        
        Args:
            X: DataFrame containing price history data
            y: Target variable (not used)
            
        Returns:
            Self
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Check for required columns
        required_cols = ['price', 'date']
        if not all(col in X.columns for col in required_cols):
            missing = [col for col in required_cols if col not in X.columns]
            raise ValueError(f"Missing required columns: {missing}")
        
        # Ensure date column is datetime
        X = X.copy()
        X['date'] = pd.to_datetime(X['date'])
        
        # Store price history by property ID if available
        if 'property_id' in X.columns:
            self.price_history = {
                prop_id: group.sort_values('date')[['date', 'price']].values
                for prop_id, group in X.groupby('property_id')
            }
        
        # Calculate market-level trends for each window
        for window in self.window_sizes:
            cutoff_date = self.reference_date - timedelta(days=window)
            recent_data = X[X['date'] >= cutoff_date]
            
            if len(recent_data) > 0:
                # Calculate average price and trend
                avg_price = recent_data['price'].mean()
                
                # Calculate daily trend
                if 'city' in X.columns:
                    # By city
                    trends_by_city = {}
                    for city, city_data in recent_data.groupby('city'):
                        if len(city_data) > 1:
                            city_data = city_data.sort_values('date')
                            daily_prices = city_data.set_index('date')['price'].resample('D').mean().fillna(method='ffill')
                            if len(daily_prices) > 1:
                                # Calculate percent change per day
                                trends_by_city[city] = daily_prices.pct_change().mean()
                    
                    self.market_trends[window] = {
                        'avg_price': avg_price,
                        'city_trends': trends_by_city
                    }
                else:
                    # Overall market
                    daily_prices = recent_data.sort_values('date').set_index('date')['price'].resample('D').mean().fillna(method='ffill')
                    if len(daily_prices) > 1:
                        trend = daily_prices.pct_change().mean()
                        self.market_trends[window] = {
                            'avg_price': avg_price,
                            'trend': trend
                        }
        
        return self
    
    def transform(self, X):
        """
        Transform properties data by adding price trend features.
        
        Args:
            X: DataFrame containing property data
            
        Returns:
            DataFrame with added price trend features
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Initialize result DataFrame
        result = pd.DataFrame(index=X.index)
        
        # If price history is available for individual properties
        if 'property_id' in X.columns and self.price_history:
            # Calculate property-specific trend features
            for idx, row in X.iterrows():
                prop_id = row['property_id']
                if prop_id in self.price_history:
                    history = self.price_history[prop_id]
                    
                    # Calculate trends for each window
                    for window in self.window_sizes:
                        window_col = f'price_trend_{window}d'
                        volatility_col = f'price_volatility_{window}d'
                        
                        cutoff_date = self.reference_date - timedelta(days=window)
                        recent_history = [
                            (date, price) for date, price in history
                            if date >= cutoff_date
                        ]
                        
                        if len(recent_history) > 1:
                            # Calculate trend (average percent change)
                            prices = [price for _, price in recent_history]
                            pct_changes = [(prices[i] - prices[i-1]) / prices[i-1] 
                                          for i in range(1, len(prices))]
                            
                            result.loc[idx, window_col] = np.mean(pct_changes)
                            result.loc[idx, volatility_col] = np.std(pct_changes)
                        else:
                            # Use market trend as fallback
                            if window in self.market_trends:
                                if 'city' in X.columns and row['city'] in self.market_trends[window].get('city_trends', {}):
                                    result.loc[idx, window_col] = self.market_trends[window]['city_trends'][row['city']]
                                elif 'trend' in self.market_trends[window]:
                                    result.loc[idx, window_col] = self.market_trends[window]['trend']
        
        # Add market-relative price features
        if 'price' in X.columns:
            for window, trends in self.market_trends.items():
                if 'city' in X.columns:
                    # By city
                    for idx, row in X.iterrows():
                        city = row['city']
                        if city in trends.get('city_trends', {}):
                            avg_price_city = trends.get('city_avg_price', {}).get(city, trends['avg_price'])
                            if avg_price_city > 0:
                                result.loc[idx, f'price_vs_market_{window}d'] = row['price'] / avg_price_city - 1
                else:
                    # Overall market
                    avg_price = trends.get('avg_price', 0)
                    if avg_price > 0:
                        result[f'price_vs_market_{window}d'] = X['price'] / avg_price - 1
        
        return result


class NeighborhoodClusterer(BaseEstimator, TransformerMixin):
    """
    Cluster properties into neighborhoods based on geographic and other features.
    
    This transformer uses unsupervised learning to group properties into
    neighborhoods or micro-markets based on location and other attributes.
    """
    
    def __init__(
        self, 
        n_clusters: int = 10, 
        cluster_method: str = 'kmeans',
        features: List[str] = None,
        random_state: int = 42,
        scaler: Optional[StandardScaler] = None
    ):
        """
        Initialize the neighborhood clusterer.
        
        Args:
            n_clusters: Number of clusters for KMeans clustering
            cluster_method: Clustering method ('kmeans' or 'dbscan')
            features: List of features to use for clustering
            random_state: Random seed for reproducibility
            scaler: Scaler for feature normalization
        """
        self.n_clusters = n_clusters
        self.cluster_method = cluster_method
        self.features = features or ['latitude', 'longitude', 'price_per_sqm']
        self.random_state = random_state
        self.scaler = scaler or StandardScaler()
        self.clusterer = None
        self.cluster_centers_ = None
        self.cluster_stats = {}
    
    def fit(self, X, y=None):
        """
        Fit the clusterer to identify neighborhoods.
        
        Args:
            X: DataFrame containing property data
            y: Target variable (not used)
            
        Returns:
            Self
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Check if all required features are available
        available_features = [f for f in self.features if f in X.columns]
        if len(available_features) < 2:
            raise ValueError(f"Insufficient features for clustering. Available: {available_features}")
        
        # Select and scale features
        X_cluster = X[available_features].copy()
        X_cluster = X_cluster.fillna(X_cluster.median())
        X_scaled = self.scaler.fit_transform(X_cluster)
        
        # Apply clustering
        if self.cluster_method.lower() == 'kmeans':
            self.clusterer = KMeans(
                n_clusters=self.n_clusters,
                random_state=self.random_state,
                n_init=10
            )
        else:  # DBSCAN
            self.clusterer = DBSCAN(
                eps=0.5,
                min_samples=5
            )
        
        # Fit the clusterer
        self.clusterer.fit(X_scaled)
        
        # Get cluster assignments
        if self.cluster_method.lower() == 'kmeans':
            labels = self.clusterer.labels_
            self.cluster_centers_ = self.scaler.inverse_transform(self.clusterer.cluster_centers_)
        else:
            labels = self.clusterer.labels_
            self.cluster_centers_ = None
        
        # Calculate statistics for each cluster
        cluster_df = X.copy()
        cluster_df['cluster'] = labels
        
        for cluster_id in sorted(set(labels)):
            if cluster_id >= 0:  # Skip noise points (-1) from DBSCAN
                cluster_data = cluster_df[cluster_df['cluster'] == cluster_id]
                
                # Basic stats for the cluster
                stats = {
                    'count': len(cluster_data),
                    'centroid': {
                        'latitude': cluster_data['latitude'].mean() if 'latitude' in X.columns else None,
                        'longitude': cluster_data['longitude'].mean() if 'longitude' in X.columns else None
                    }
                }
                
                # Additional stats if price data is available
                if 'price' in X.columns:
                    stats['avg_price'] = cluster_data['price'].mean()
                    stats['median_price'] = cluster_data['price'].median()
                
                if 'price_per_sqm' in X.columns:
                    stats['avg_price_per_sqm'] = cluster_data['price_per_sqm'].mean()
                    stats['median_price_per_sqm'] = cluster_data['price_per_sqm'].median()
                
                self.cluster_stats[cluster_id] = stats
        
        return self
    
    def transform(self, X):
        """
        Transform properties by adding neighborhood cluster features.
        
        Args:
            X: DataFrame containing property data
            
        Returns:
            DataFrame with added neighborhood features
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if self.clusterer is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")
        
        # Initialize result DataFrame
        result = pd.DataFrame(index=X.index)
        
        # Check if all required features are available
        available_features = [f for f in self.features if f in X.columns]
        if len(available_features) < 2:
            # Can't cluster, return empty result
            logger.warning(f"Insufficient features for clustering. Available: {available_features}")
            return result
        
        # Select and scale features
        X_cluster = X[available_features].copy()
        X_cluster = X_cluster.fillna(X_cluster.median())
        X_scaled = self.scaler.transform(X_cluster)
        
        # Predict clusters
        if self.cluster_method.lower() == 'kmeans':
            labels = self.clusterer.predict(X_scaled)
        else:  # DBSCAN doesn't have predict, use fit_predict
            labels = self.clusterer.fit_predict(X_scaled)
        
        # Add cluster assignment
        result['neighborhood_cluster'] = labels
        
        # Add distance to cluster center for KMeans
        if self.cluster_method.lower() == 'kmeans':
            distances = self.clusterer.transform(X_scaled)
            result['distance_to_cluster_center'] = np.min(distances, axis=1)
        
        # Add cluster statistics
        for cluster_id, stats in self.cluster_stats.items():
            mask = result['neighborhood_cluster'] == cluster_id
            if mask.sum() > 0:
                if 'avg_price' in stats:
                    result.loc[mask, 'neighborhood_avg_price'] = stats['avg_price']
                if 'avg_price_per_sqm' in stats:
                    result.loc[mask, 'neighborhood_avg_price_per_sqm'] = stats['avg_price_per_sqm']
        
        # Calculate price premium relative to neighborhood
        if 'price' in X.columns and 'neighborhood_avg_price' in result.columns:
            result['price_premium_vs_neighborhood'] = X['price'] / result['neighborhood_avg_price'] - 1
        
        if 'price_per_sqm' in X.columns and 'neighborhood_avg_price_per_sqm' in result.columns:
            result['price_per_sqm_premium'] = X['price_per_sqm'] / result['neighborhood_avg_price_per_sqm'] - 1
        
        return result
    
    def visualize_clusters(self, X, output_path: Optional[str] = None, figsize: Tuple[int, int] = (12, 8)):
        """
        Visualize the neighborhood clusters on a scatter plot.
        
        Args:
            X: DataFrame containing property data
            output_path: Path to save the visualization (if None, display only)
            figsize: Figure size (width, height) in inches
            
        Returns:
            matplotlib Figure object
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if 'latitude' not in X.columns or 'longitude' not in X.columns:
            raise ValueError("DataFrame must contain 'latitude' and 'longitude' columns")
        
        if self.clusterer is None:
            raise ValueError("Clusterer not fitted. Call fit() first.")
        
        # Predict clusters if needed
        if 'neighborhood_cluster' not in X.columns:
            # Select and scale features
            available_features = [f for f in self.features if f in X.columns]
            X_cluster = X[available_features].copy()
            X_cluster = X_cluster.fillna(X_cluster.median())
            X_scaled = self.scaler.transform(X_cluster)
            
            # Predict clusters
            if self.cluster_method.lower() == 'kmeans':
                labels = self.clusterer.predict(X_scaled)
            else:  # DBSCAN
                labels = self.clusterer.fit_predict(X_scaled)
        else:
            labels = X['neighborhood_cluster']
        
        # Create plot
        plt.figure(figsize=figsize)
        
        # Plot points, colored by cluster
        scatter = plt.scatter(
            X['longitude'],
            X['latitude'],
            c=labels,
            cmap='tab10',
            alpha=0.6,
            s=50
        )
        
        # Plot cluster centers for KMeans
        if self.cluster_method.lower() == 'kmeans' and self.cluster_centers_ is not None:
            center_idx = [i for i, f in enumerate(self.features) if f == 'longitude'][0]
            center_idy = [i for i, f in enumerate(self.features) if f == 'latitude'][0]
            
            plt.scatter(
                self.cluster_centers_[:, center_idx],
                self.cluster_centers_[:, center_idy],
                s=200,
                marker='X',
                c='red',
                alpha=0.8,
                label='Cluster Centers'
            )
        
        # Add title and labels
        plt.title(f'Neighborhood Clusters ({self.cluster_method.title()})')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.colorbar(scatter, label='Cluster')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save or display
        if output_path:
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved cluster visualization to {output_path}")
        
        return plt.gcf()


class SentimentAnalysisTransformer(BaseEstimator, TransformerMixin):
    """
    Extract sentiment scores from property descriptions.
    
    This transformer analyzes the sentiment of property descriptions to
    extract features related to positivity, subjectivity, and key themes.
    """
    
    def __init__(self, language: str = 'italian', use_pretrained: bool = True):
        """
        Initialize the sentiment analyzer.
        
        Args:
            language: Language for sentiment analysis ('italian', 'english', etc.)
            use_pretrained: Whether to use pretrained models
        """
        self.language = language
        self.use_pretrained = use_pretrained
        self._initialize_nlp()
        
        # Dictionaries for positive and negative terms in real estate listings
        self.positive_terms = {
            'italian': [
                'luminoso', 'spazioso', 'panoramico', 'ristrutturato', 'moderno',
                'elegante', 'prestigioso', 'lussuoso', 'tranquillo', 'silenzioso',
                'esclusivo', 'pregiato', 'signorile', 'raffinato', 'curato',
                'ampio', 'soleggiato', 'arioso', 'accogliente', 'comodo',
                'strategico', 'centrale', 'ben collegato', 'servito', 'vicinanza'
            ],
            'english': [
                'bright', 'spacious', 'panoramic', 'renovated', 'modern',
                'elegant', 'prestigious', 'luxurious', 'quiet', 'silent',
                'exclusive', 'valuable', 'refined', 'well-maintained', 'curated',
                'ample', 'sunny', 'airy', 'cozy', 'comfortable',
                'strategic', 'central', 'well-connected', 'served', 'proximity'
            ]
        }
        
        self.negative_terms = {
            'italian': [
                'rumoroso', 'piccolo', 'stretto', 'buio', 'vecchio',
                'datato', 'da ristrutturare', 'umido', 'trascurato', 'economico',
                'semplice', 'trafficato', 'periferico', 'lontano', 'isolato'
            ],
            'english': [
                'noisy', 'small', 'narrow', 'dark', 'old',
                'dated', 'needs renovation', 'damp', 'neglected', 'cheap',
                'simple', 'busy', 'peripheral', 'far', 'isolated'
            ]
        }
        
        # Feature names
        self.feature_names = [
            'sentiment_score', 
            'positive_term_count', 
            'negative_term_count',
            'subjectivity_score',
            'hype_factor'
        ]
    
    def _initialize_nlp(self):
        """Initialize NLP components based on language."""
        self.nlp_available = False
        
        # Try to import spaCy
        try:
            import spacy
            self.nlp_available = True
            
            # Try to load language model
            try:
                if self.language == 'italian':
                    self.nlp = spacy.load('it_core_news_sm')
                elif self.language == 'english':
                    self.nlp = spacy.load('en_core_web_sm')
                else:
                    logger.warning(f"Language model for '{self.language}' not available")
                    self.nlp_available = False
            except:
                logger.warning(f"Could not load spaCy model for {self.language}")
                self.nlp_available = False
        except ImportError:
            logger.warning("spaCy not available. Using simple lexicon-based approach.")
        
        # Try to import TextBlob for sentiment analysis
        try:
            from textblob import TextBlob
            self.textblob_available = True
            self.TextBlob = TextBlob
        except ImportError:
            logger.warning("TextBlob not available. Using simple lexicon-based approach.")
            self.textblob_available = False
    
    def fit(self, X, y=None):
        """Fit method (no-op for this transformer)."""
        return self
    
    def transform(self, X):
        """
        Transform property descriptions with sentiment features.
        
        Args:
            X: DataFrame or Series containing description text
            
        Returns:
            DataFrame with sentiment features
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
        
        # Create an output dataframe
        result = pd.DataFrame(index=X.index, columns=self.feature_names)
        
        # Process each description
        for idx, desc in descriptions.items():
            # Count positive and negative terms
            lang = self.language if self.language in self.positive_terms else 'english'
            
            pos_count = sum(1 for term in self.positive_terms[lang] if re.search(rf'\b{term}\b', desc.lower()))
            neg_count = sum(1 for term in self.negative_terms[lang] if re.search(rf'\b{term}\b', desc.lower()))
            
            result.loc[idx, 'positive_term_count'] = pos_count
            result.loc[idx, 'negative_term_count'] = neg_count
            
            # Calculate lexicon-based sentiment score
            total_terms = pos_count + neg_count
            if total_terms > 0:
                result.loc[idx, 'sentiment_score'] = (pos_count - neg_count) / total_terms
            else:
                result.loc[idx, 'sentiment_score'] = 0
            
            # Additional features if NLP is available
            if self.nlp_available:
                doc = self.nlp(desc)
                
                # Count adjectives and adverbs for subjectivity
                adj_adv_count = len([token for token in doc if token.pos_ in ('ADJ', 'ADV')])
                result.loc[idx, 'subjectivity_score'] = adj_adv_count / len(doc) if len(doc) > 0 else 0
                
                # Detect superlatives and intensifiers for hype factor
                superlative_count = len([token for token in doc if token.tag_ in ('JJS', 'RBS')])
                intensifier_count = len([token for token in doc if token.lower_ in ('molto', 'assai', 'estremamente', 'davvero')])
                result.loc[idx, 'hype_factor'] = (superlative_count + intensifier_count) / len(doc) if len(doc) > 0 else 0
            elif self.textblob_available:
                # Use TextBlob for sentiment analysis
                if self.language == 'english':
                    blob = self.TextBlob(desc)
                    result.loc[idx, 'subjectivity_score'] = blob.sentiment.subjectivity
                    
                    # Use TextBlob polarity as additional input for sentiment score
                    result.loc[idx, 'sentiment_score'] = (result.loc[idx, 'sentiment_score'] + blob.sentiment.polarity) / 2
                    
                    # Simple heuristic for hype factor
                    exclamation_count = desc.count('!')
                    uppercase_ratio = sum(1 for c in desc if c.isupper()) / len(desc) if len(desc) > 0 else 0
                    result.loc[idx, 'hype_factor'] = (exclamation_count / 10 + uppercase_ratio) / 2
            else:
                # Fallback for subjectivity and hype
                exclamation_count = desc.count('!')
                result.loc[idx, 'subjectivity_score'] = 0.5  # Neutral default
                result.loc[idx, 'hype_factor'] = exclamation_count / 10
        
        return result
    
    def get_feature_names_out(self):
        """Return feature names for the transformer output."""
        return self.feature_names


class EnergyEfficiencyTransformer(BaseEstimator, TransformerMixin):
    """
    Extract and transform energy efficiency related features.
    
    This transformer extracts energy class information from property data
    and converts it into numerical features useful for modeling.
    """
    
    def __init__(self):
        """Initialize the energy efficiency transformer."""
        # Mapping of energy classes to numerical values
        self.energy_class_map = {
            'A4': 10,
            'A3': 9,
            'A2': 8,
            'A1': 7,
            'A': 6,
            'B': 5,
            'C': 4,
            'D': 3,
            'E': 2,
            'F': 1,
            'G': 0,
            'exempt': -1,
            'unknown': -1
        }
        
        # Regular expressions for extracting energy information
        self.energy_regex = {
            'class': r'classe\s+energetica\s*[:\-]?\s*([A-G][1-4]?)',
            'consumption': r'(\d+[.,]?\d*)\s*kWh\/m²a'
        }
    
    def fit(self, X, y=None):
        """Fit method (no-op for this transformer)."""
        return self
    
    def transform(self, X):
        """
        Transform property data by extracting energy efficiency features.
        
        Args:
            X: DataFrame containing property data
            
        Returns:
            DataFrame with energy efficiency features
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Initialize result DataFrame
        result = pd.DataFrame(index=X.index)
        
        # Check if energy class column exists
        if 'energy_class' in X.columns:
            # Direct mapping from existing column
            energy_class = X['energy_class'].str.upper()
            result['energy_class_value'] = energy_class.map(self.energy_class_map).fillna(-1)
            
            # Create binary indicators for high-efficiency classes
            result['is_high_efficiency'] = result['energy_class_value'] >= 6  # A or better
            result['is_low_efficiency'] = result['energy_class_value'] <= 2   # E or worse
        else:
            # Try to extract from description
            if 'description' in X.columns:
                descriptions = X['description'].fillna('')
                
                # Extract energy class from description
                energy_classes = descriptions.str.extract(self.energy_regex['class'], flags=re.IGNORECASE)
                if energy_classes.notna().any().any():
                    energy_classes = energy_classes.fillna('unknown').iloc[:, 0].str.upper()
                    result['energy_class_value'] = energy_classes.map(self.energy_class_map).fillna(-1)
                    
                    # Create binary indicators
                    result['is_high_efficiency'] = result['energy_class_value'] >= 6
                    result['is_low_efficiency'] = result['energy_class_value'] <= 2
                
                # Extract energy consumption if available
                energy_consumption = descriptions.str.extract(self.energy_regex['consumption'], flags=re.IGNORECASE)
                if energy_consumption.notna().any().any():
                    # Convert to numeric
                    consumption = energy_consumption.iloc[:, 0].str.replace(',', '.').astype(float)
                    result['energy_consumption_kwh_m2a'] = consumption
        
        # Check for heating system information
        for heating_col in ['heating_type', 'heating', 'riscaldamento']:
            if heating_col in X.columns:
                # Create indicators for common heating systems
                heating_info = X[heating_col].fillna('').str.lower()
                
                result['has_autonomous_heating'] = heating_info.str.contains('autonomo|individuale')
                result['has_central_heating'] = heating_info.str.contains('centralizzato|condominiale')
                result['has_floor_heating'] = heating_info.str.contains('pavimento')
                result['has_gas_heating'] = heating_info.str.contains('gas|metano')
                result['has_heat_pump'] = heating_info.str.contains('pompa di calore|heat pump')
                break
        
        # Check for renewable energy features
        if 'description' in X.columns:
            descriptions = X['description'].fillna('').str.lower()
            
            result['has_solar_panels'] = descriptions.str.contains(
                'pannelli solari|pannello solare|fotovoltaico|fotovoltaici'
            )
            
            result['has_renewable_energy'] = descriptions.str.contains(
                'energia rinnovabile|rinnovabili|sostenibile|ecologico'
            )
        
        return result


class ExternalDataEnricher(BaseEstimator, TransformerMixin):
    """
    Enrich property data with external data sources.
    
    This transformer integrates external data sources such as
    census data, POI data, and other contextual information.
    """
    
    def __init__(
        self, 
        external_data_path: Optional[str] = None,
        cache_dir: str = 'data/external_cache',
        poi_radius_km: float = 1.0
    ):
        """
        Initialize the external data enricher.
        
        Args:
            external_data_path: Path to external data files
            cache_dir: Directory for caching external API results
            poi_radius_km: Radius in km for POI searches
        """
        self.external_data_path = Path(external_data_path) if external_data_path else None
        self.cache_dir = Path(cache_dir)
        self.poi_radius_km = poi_radius_km
        self.census_data = None
        self.poi_data = None
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_external_data(self):
        """Load external data from files."""
        if self.external_data_path and self.external_data_path.exists():
            # Try to load census data
            census_path = self.external_data_path / 'census_data.csv'
            if census_path.exists():
                try:
                    self.census_data = pd.read_csv(census_path)
                    logger.info(f"Loaded census data from {census_path}")
                except Exception as e:
                    logger.warning(f"Failed to load census data: {e}")
            
            # Try to load POI data
            poi_path = self.external_data_path / 'poi_data.csv'
            if poi_path.exists():
                try:
                    self.poi_data = pd.read_csv(poi_path)
                    logger.info(f"Loaded POI data from {poi_path}")
                except Exception as e:
                    logger.warning(f"Failed to load POI data: {e}")
    
    def fit(self, X, y=None):
        """
        Fit the enricher by loading external data.
        
        Args:
            X: DataFrame containing property data
            y: Target variable (not used)
            
        Returns:
            Self
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Load external data
        self._load_external_data()
        
        return self
    
    def transform(self, X):
        """
        Transform property data by adding external data features.
        
        Args:
            X: DataFrame containing property data
            
        Returns:
            DataFrame with added external data features
        """
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        # Initialize result DataFrame
        result = pd.DataFrame(index=X.index)
        
        # Check if we have geo coordinates
        if 'latitude' not in X.columns or 'longitude' not in X.columns:
            logger.warning("Missing latitude/longitude columns, can't add geo-based features")
            return result
        
        # Add census data features if available
        if self.census_data is not None and 'zipcode' in X.columns and 'zipcode' in self.census_data.columns:
            # Join on zipcode
            census_features = [col for col in self.census_data.columns if col != 'zipcode']
            
            for feature in census_features:
                # Create a mapping from zipcode to feature
                zipcode_mapping = dict(zip(self.census_data['zipcode'], self.census_data[feature]))
                
                # Map the feature to the result DataFrame
                result[f'census_{feature}'] = X['zipcode'].map(zipcode_mapping)
        
        # Add POI data features if available
        if self.poi_data is not None and all(col in self.poi_data.columns for col in ['latitude', 'longitude', 'category']):
            # Calculate distance to nearest POIs for each category
            poi_categories = self.poi_data['category'].unique()
            
            for category in poi_categories:
                category_pois = self.poi_data[self.poi_data['category'] == category]
                
                if len(category_pois) > 0:
                    # Calculate distances from each property to each POI in this category
                    distances = np.zeros((len(X), len(category_pois)))
                    
                    for i, (_, prop) in enumerate(X.iterrows()):
                        for j, (_, poi) in enumerate(category_pois.iterrows()):
                            # Calculate Haversine distance
                            distances[i, j] = self._haversine_distance(
                                prop['latitude'], prop['longitude'],
                                poi['latitude'], poi['longitude']
                            )
                    
                    # Get minimum distance for each property
                    min_distances = np.min(distances, axis=1)
                    
                    # Add as feature
                    safe_category = category.lower().replace(' ', '_')
                    result[f'distance_to_{safe_category}_km'] = min_distances
                    
                    # Add count of POIs within radius
                    poi_counts = np.sum(distances <= self.poi_radius_km, axis=1)
                    result[f'{safe_category}_count_within_{self.poi_radius_km}km'] = poi_counts
        
        # Try to enrich with external APIs if available
        try:
            # Weather data
            if 'latitude' in X.columns and 'longitude' in X.columns:
                self._add_weather_features(X, result)
            
            # School data
            self._add_school_features(X, result)
            
            # Crime data
            self._add_crime_features(X, result)
        except Exception as e:
            logger.warning(f"Error enriching with external APIs: {e}")
        
        return result
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the Haversine distance between points.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
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
    
    def _add_weather_features(self, X, result):
        """
        Add weather data features from external API.
        
        Args:
            X: Input DataFrame
            result: Result DataFrame to add features to
        """
        # This is a placeholder - in a real implementation, this would call a weather API
        # or use cached weather data for the locations in X
        pass
    
    def _add_school_features(self, X, result):
        """
        Add school quality data from external API.
        
        Args:
            X: Input DataFrame
            result: Result DataFrame to add features to
        """
        # This is a placeholder - in a real implementation, this would call an education API
        # or use cached school data for the locations in X
        pass
    
    def _add_crime_features(self, X, result):
        """
        Add crime statistics from external API.
        
        Args:
            X: Input DataFrame
            result: Result DataFrame to add features to
        """
        # This is a placeholder - in a real implementation, this would call a crime statistics API
        # or use cached crime data for the locations in X
        pass


def create_enhanced_feature_pipeline(
    include_price_trends: bool = True,
    include_neighborhoods: bool = True,
    include_sentiment: bool = True,
    include_energy: bool = True,
    include_external_data: bool = False,
    external_data_path: Optional[str] = None,
    n_clusters: int = 10
):
    """
    Create a comprehensive pipeline for enhanced feature engineering.
    
    This function creates a pipeline that combines multiple advanced feature
    engineering transformers for comprehensive feature extraction.
    
    Args:
        include_price_trends: Whether to include price trend analysis
        include_neighborhoods: Whether to include neighborhood clustering
        include_sentiment: Whether to include sentiment analysis
        include_energy: Whether to include energy efficiency features
        include_external_data: Whether to include external data enrichment
        external_data_path: Path to external data files
        n_clusters: Number of neighborhood clusters
        
    Returns:
        A scikit-learn Pipeline for enhanced feature engineering
    """
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    
    # Define transformers
    transformers = []
    
    # Basic advanced features from the original module
    transformers.append(
        ('description_features', DescriptionFeatureExtractor(), ['description'])
    )
    
    transformers.append(
        ('geographic_features', GeographicFeatureTransformer(), ['latitude', 'longitude', 'city'])
    )
    
    transformers.append(
        ('time_features', TimeFeatureTransformer(), ['date_posted', 'date_updated'])
    )
    
    # Add enhanced features
    if include_price_trends:
        transformers.append(
            ('price_trends', PriceTrendAnalyzer(), ['price', 'date', 'property_id', 'city'])
        )
    
    if include_neighborhoods:
        transformers.append(
            ('neighborhood_clusters', NeighborhoodClusterer(n_clusters=n_clusters), 
             ['latitude', 'longitude', 'price_per_sqm'])
        )
    
    if include_sentiment:
        transformers.append(
            ('sentiment_analysis', SentimentAnalysisTransformer(), ['description'])
        )
    
    if include_energy:
        transformers.append(
            ('energy_efficiency', EnergyEfficiencyTransformer(), 
             ['energy_class', 'description', 'heating_type'])
        )
    
    if include_external_data:
        transformers.append(
            ('external_data', ExternalDataEnricher(external_data_path=external_data_path),
             ['latitude', 'longitude', 'zipcode'])
        )
    
    # Create the column transformer
    feature_engineering = ColumnTransformer(
        transformers=transformers,
        remainder='passthrough'
    )
    
    # Create the pipeline
    pipeline = Pipeline([
        ('enhanced_features', feature_engineering)
    ])
    
    return pipeline


def feature_importance_analysis(
    model, 
    feature_names, 
    top_n: int = 20, 
    output_path: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 8)
):
    """
    Analyze and visualize feature importance from a trained model.
    
    Args:
        model: Trained model with feature_importances_ or coef_ attribute
        feature_names: List of feature names
        top_n: Number of top features to display
        output_path: Path to save the visualization
        figsize: Figure size (width, height) in inches
        
    Returns:
        Tuple of (DataFrame with feature importances, matplotlib Figure)
    """
    # Extract feature importance
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    elif hasattr(model, 'coef_'):
        importances = np.abs(model.coef_)
        if importances.ndim > 1:
            importances = importances[0]
    else:
        raise ValueError("Model doesn't have feature_importances_ or coef_ attribute")
    
    # Create DataFrame with feature importances
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    })
    
    # Sort by importance
    importance_df = importance_df.sort_values('importance', ascending=False)
    
    # Plot top N features
    top_features = importance_df.head(top_n)
    
    plt.figure(figsize=figsize)
    sns.barplot(x='importance', y='feature', data=top_features)
    plt.title(f'Top {top_n} Most Important Features')
    plt.xlabel('Importance')
    plt.ylabel('Feature')
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved feature importance visualization to {output_path}")
    
    return importance_df, plt.gcf()


def extract_year_built(description_text):
    """
    Extract the year built from property description text.
    
    Args:
        description_text: Property description text
        
    Returns:
        Extracted year or None if not found
    """
    # Regular expression patterns for different formats
    patterns = [
        r'costruito\s+nel\s+(\d{4})',  # costruito nel 1990
        r'costruzione\s+del\s+(\d{4})',  # costruzione del 1990
        r'edificato\s+nel\s+(\d{4})',  # edificato nel 1990
        r'anno\s+(\d{4})',  # anno 1990
        r'anno\s+di\s+costruzione\s+(\d{4})',  # anno di costruzione 1990
        r'del\s+(\d{4})',  # del 1990 (more prone to false positives)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description_text, re.IGNORECASE)
        if match:
            try:
                year = int(match.group(1))
                # Validate the year is reasonable
                current_year = datetime.now().year
                if 1800 <= year <= current_year:
                    return year
            except:
                pass
    
    return None


def extract_renovation_year(description_text):
    """
    Extract the renovation year from property description text.
    
    Args:
        description_text: Property description text
        
    Returns:
        Extracted renovation year or None if not found
    """
    # Regular expression patterns for different formats
    patterns = [
        r'ristrutturato\s+nel\s+(\d{4})',  # ristrutturato nel 1990
        r'ristrutturazione\s+del\s+(\d{4})',  # ristrutturazione del 1990
        r'rinnovato\s+nel\s+(\d{4})',  # rinnovato nel 1990
        r'ristrutturazione\s+completa\s+nel\s+(\d{4})',  # ristrutturazione completa nel 1990
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description_text, re.IGNORECASE)
        if match:
            try:
                year = int(match.group(1))
                # Validate the year is reasonable
                current_year = datetime.now().year
                if 1950 <= year <= current_year:
                    return year
            except:
                pass
    
    return None


def calculate_property_age_features(X):
    """
    Calculate property age-related features.
    
    Args:
        X: DataFrame with property data including description
        
    Returns:
        DataFrame with added age-related features
    """
    if not isinstance(X, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    
    if 'description' not in X.columns:
        return pd.DataFrame(index=X.index)
    
    result = pd.DataFrame(index=X.index)
    current_year = datetime.now().year
    
    # Extract years from description
    if 'description' in X.columns:
        descriptions = X['description'].fillna('')
        
        # Extract year built
        result['year_built'] = descriptions.apply(extract_year_built)
        
        # Extract renovation year
        result['renovation_year'] = descriptions.apply(extract_renovation_year)
    
    # Calculate age features if year_built is available
    mask = result['year_built'].notna()
    if mask.sum() > 0:
        result.loc[mask, 'property_age'] = current_year - result.loc[mask, 'year_built']
        
        # Create age categories
        age_bins = [0, 5, 10, 20, 30, 50, 100, float('inf')]
        age_labels = ['New (0-5)', 'Recent (5-10)', 'Modern (10-20)', 
                      'Established (20-30)', 'Mature (30-50)', 'Historic (50-100)', 'Ancient (100+)']
        
        result.loc[mask, 'age_category'] = pd.cut(
            result.loc[mask, 'property_age'],
            bins=age_bins,
            labels=age_labels
        )
    
    # Calculate time since renovation
    mask = result['renovation_year'].notna()
    if mask.sum() > 0:
        result.loc[mask, 'years_since_renovation'] = current_year - result.loc[mask, 'renovation_year']
    
    # Calculate if the property has been renovated relative to its age
    mask = (result['year_built'].notna()) & (result['renovation_year'].notna())
    if mask.sum() > 0:
        # Calculate what percentage of the property's age has passed since renovation
        age = current_year - result.loc[mask, 'year_built']
        total_lifespan = age
        years_since_reno = current_year - result.loc[mask, 'renovation_year']
        
        result.loc[mask, 'renovation_recency'] = 1 - (years_since_reno / total_lifespan)
        
        # Clean up any invalid values
        result.loc[result['renovation_recency'] < 0, 'renovation_recency'] = 0
        result.loc[result['renovation_recency'] > 1, 'renovation_recency'] = 1
    
    return result
