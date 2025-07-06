# Using the API Immobiliare Library with Machine Learning

The API Immobiliare package now includes dedicated modules for preprocessing real estate data and applying machine learning techniques. This example shows how to use these modules together with the core API to build a complete real estate price prediction workflow.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Data Collection](#data-collection)
- [Data Preprocessing](#data-preprocessing)
- [Machine Learning Models](#machine-learning-models)
- [Full Example](#full-example)
- [Advanced Usage](#advanced-usage)

## Installation

First, ensure you have all the required packages:

```bash
pip install -r requirements.txt
```

## Basic Usage

Here's a simple example of how to use the API Immobiliare library with the machine learning modules:

```python
from immob.api_immobiliare.retrievers import ImmobiliareAdRetriever
from immob.api_immobiliare.data_manager import RealEstateDataManager
from immob.api_immobiliare.preprocessing import create_preprocessing_pipeline
from immob.api_immobiliare.ml_utils import train_multiple_models, evaluate_model

# 1. Collect real estate data
retriever = ImmobiliareAdRetriever()
data_manager = RealEstateDataManager(retriever)

# Define search parameters
search_params = {
    "city": "Genova", 
    "zones": ["Centro", "Castelletto"],
    "property_type": "apartment",
    "transaction_type": "sell"
}

# Fetch and save data
ads_df = data_manager.fetch_and_save_ads(
    search_params, 
    output_format="pandas"  # Return as pandas DataFrame
)

# 2. Preprocess the data
pipeline = create_preprocessing_pipeline()
X = pipeline.fit_transform(ads_df)
y = ads_df['price']

# 3. Train and evaluate models
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
models = train_multiple_models(X_train, y_train)

# Evaluate the best model (e.g., Random Forest)
results = evaluate_model(models['random_forest'], X_test, y_test)
print(f"R² Score: {results['r2']}")
print(f"Mean Absolute Error: {results['mae']}")
```

## Data Collection

The library provides a flexible system for collecting real estate data:

```python
# Basic search with minimum parameters
basic_params = {
    "city": "Milano",
    "transaction_type": "sell"
}

# Advanced search with detailed parameters
advanced_params = {
    "city": "Genova",
    "zones": ["Centro", "Castelletto", "Foce"],
    "property_type": "apartment",
    "transaction_type": "sell",
    "price_min": 100000,
    "price_max": 400000,
    "size_min": 70,
    "rooms_min": 2,
    "bathrooms_min": 1
}

# Fetch data with the advanced parameters
data_manager = RealEstateDataManager(ImmobiliareAdRetriever())
ads_df = data_manager.fetch_and_save_ads(
    advanced_params, 
    output_format="pandas"
)
```

## Data Preprocessing

The `preprocessing` module offers tools to prepare real estate data for machine learning:

```python
from immob.api_immobiliare.preprocessing import (
    create_preprocessing_pipeline,
    FloorNormalizer,
    GarageStandardizer,
    extract_features_from_description
)

# Create a standard preprocessing pipeline
pipeline = create_preprocessing_pipeline()

# Or build a custom pipeline
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

# Define custom preprocessing steps
custom_pipeline = Pipeline([
    ('floor_norm', FloorNormalizer()),
    ('garage_std', GarageStandardizer()),
    ('feature_extractor', ColumnTransformer([
        ('num_features', StandardScaler(), ['size', 'rooms', 'bathrooms', 'floor']),
        ('cat_features', OneHotEncoder(handle_unknown='ignore'), ['property_type', 'condition'])
    ])),
    ('imputer', SimpleImputer(strategy='median'))
])

# Apply preprocessing
X_processed = custom_pipeline.fit_transform(ads_df)
```

## Machine Learning Models

The `ml_utils` module provides functions for training, evaluating, and fine-tuning machine learning models:

```python
from immob.api_immobiliare.ml_utils import (
    train_multiple_models,
    evaluate_model,
    select_features_by_importance,
    plot_feature_importance,
    hyperparameter_tuning
)

# Train multiple models at once
models = train_multiple_models(X_train, y_train)

# Evaluate all models
for name, model in models.items():
    results = evaluate_model(model, X_test, y_test)
    print(f"{name}: R² = {results['r2']:.3f}, MAE = {results['mae']:.3f}")

# Select the most important features
X_selected = select_features_by_importance(models['random_forest'], X_train, num_features=10)

# Plot feature importance
plot_feature_importance(models['random_forest'], feature_names=X.columns)

# Tune hyperparameters
best_model = hyperparameter_tuning(
    X_train, y_train,
    model_type='random_forest',
    param_grid={
        'n_estimators': [100, 200, 300],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10]
    }
)
```

## Full Example

Here's a complete example showing how to use all components together:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

from immob.api_immobiliare.retrievers import ImmobiliareAdRetriever
from immob.api_immobiliare.data_manager import RealEstateDataManager
from immob.api_immobiliare.preprocessing import create_preprocessing_pipeline
from immob.api_immobiliare.ml_utils import (
    train_multiple_models,
    evaluate_model,
    select_features_by_importance,
    plot_feature_importance
)

# 1. Data Collection
retriever = ImmobiliareAdRetriever()
data_manager = RealEstateDataManager(retriever)

search_params = {
    "city": "Genova",
    "zones": ["Centro", "Castelletto", "Foce", "Albaro"],
    "property_type": "apartment",
    "transaction_type": "sell",
    "price_max": 500000
}

# Collect data (or load from file if already saved)
try:
    ads_df = pd.read_csv("genova_apartments.csv")
    print("Loaded data from file")
except FileNotFoundError:
    print("Collecting new data...")
    ads_df = data_manager.fetch_and_save_ads(
        search_params,
        output_format="pandas"
    )
    ads_df.to_csv("genova_apartments.csv", index=False)
    print(f"Collected {len(ads_df)} advertisements")

# 2. Data Preprocessing
print("\nPreprocessing data...")
pipeline = create_preprocessing_pipeline()
X = pipeline.fit_transform(ads_df)
y = ads_df['price']

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Training set: {X_train.shape[0]} samples")
print(f"Test set: {X_test.shape[0]} samples")

# 3. Model Training
print("\nTraining models...")
models = train_multiple_models(X_train, y_train)

# 4. Model Evaluation
print("\nModel evaluation:")
for name, model in models.items():
    results = evaluate_model(model, X_test, y_test)
    print(f"{name}: R² = {results['r2']:.3f}, MAE = {results['mae']:.3f}")

# 5. Feature Importance
best_model = models['random_forest']  # Usually the best performer
plot_feature_importance(best_model, feature_names=X.columns)

# 6. Select Important Features
X_selected = select_features_by_importance(best_model, X, num_features=10)
print(f"\nSelected {X_selected.shape[1]} most important features")

# 7. Retrain with Selected Features
X_train_selected, X_test_selected, y_train, y_test = train_test_split(
    X_selected, y, test_size=0.2, random_state=42
)

print("\nRetraining with selected features...")
models_selected = train_multiple_models(X_train_selected, y_train)

# Evaluate again
print("\nModel evaluation with selected features:")
for name, model in models_selected.items():
    results = evaluate_model(model, X_test_selected, y_test)
    print(f"{name}: R² = {results['r2']:.3f}, MAE = {results['mae']:.3f}")

# 8. Save the best model
import joblib
joblib.dump(models_selected['random_forest'], 'real_estate_price_model.pkl')
print("\nSaved best model to 'real_estate_price_model.pkl'")
```

## Advanced Usage

You can extend the functionality with custom components:

```python
from sklearn.base import BaseEstimator, TransformerMixin
from immob.api_immobiliare.preprocessing import create_preprocessing_pipeline

# Create a custom transformer
class NeighborhoodPriceEncoder(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.neighborhood_prices = {}
        
    def fit(self, X, y=None):
        # Calculate average price by neighborhood
        for neighborhood in X['neighborhood'].unique():
            mask = X['neighborhood'] == neighborhood
            self.neighborhood_prices[neighborhood] = X.loc[mask, 'price'].mean()
        return self
        
    def transform(self, X):
        X_copy = X.copy()
        X_copy['neighborhood_avg_price'] = X_copy['neighborhood'].map(self.neighborhood_prices)
        # Fill unknown neighborhoods with global average
        X_copy['neighborhood_avg_price'].fillna(sum(self.neighborhood_prices.values()) / len(self.neighborhood_prices), inplace=True)
        return X_copy

# Get the default pipeline
pipeline = create_preprocessing_pipeline()

# Add your custom transformer
from sklearn.pipeline import Pipeline
extended_pipeline = Pipeline([
    ('standard_preprocessing', pipeline),
    ('neighborhood_encoder', NeighborhoodPriceEncoder())
])

# Use the extended pipeline
X_processed = extended_pipeline.fit_transform(ads_df)
```

For more details, refer to the module documentation and API reference.
