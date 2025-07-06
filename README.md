# WebScraping Projects

This repository contains various web scraping and data processing tools.

## Projects

### House Crawler Chrome Extension
A Chrome extension for interactive web scraping of property listings.

### Real Estate Data Processing

#### API Immobiliare - OOP Framework
A modular object-oriented framework for collecting, analyzing, and processing real estate data.

Located in: `immob/api_immobiliare/`

Components:
- **Core Modules**
  - `real_estate_models.py`: Pydantic data models for real estate ads
  - `retrievers.py`: Abstract and concrete classes for fetching ads from different sources
  - `data_manager.py`: Manages data collection and storage operations
  - `config.py`: Configuration utilities and helper functions
  - `fetch_ads_cli.py`: Command-line interface for ad retrieval

- **Analysis & ML Modules**
  - `preprocessing.py`: Data preprocessing utilities for ML
  - `ml_utils.py`: Machine learning model training and evaluation
  - `analyze_real_estate_data.py`: Data analysis and visualization

- **Utility Modules**
  - `sqlite_helpers.py`: SQLite database operations
  - `helpers.py`: General purpose helper functions
  - Legacy modules for backward compatibility

Features:
- Object-oriented design with abstract interfaces
- Support for multiple real estate sites (currently implements immobiliare.it)
- Multiple storage formats (CSV, JSON, SQLite, Cosmos DB)
- Data preprocessing pipelines for machine learning
- ML model training and evaluation utilities
- Feature importance analysis and selection
- Customizable via command-line or Python API

Setup:
1. Copy `.env.example` to `.env` and fill in your credentials (if using Cosmos DB)
2. Install requirements: `pip install -r immob/api_immobiliare/requirements.txt`

Example usage - Command Line:
```bash
# Basic usage (saves to CSV by default)
python -m immob.api_immobiliare.fetch_ads_cli

# Specify city and zones
python -m immob.api_immobiliare.fetch_ads_cli --city genova --zones "Centro,Castelletto" --output-format csv

# Specify price range and property details
python -m immob.api_immobiliare.fetch_ads_cli --city milano --price-min 200000 --price-max 500000 --rooms-min 2
```

Example usage - Python API:
```python
from immob.api_immobiliare.retrievers import ImmobiliareAdRetriever
from immob.api_immobiliare.data_manager import RealEstateDataManager

# Create a retriever for immobiliare.it
retriever = ImmobiliareAdRetriever()
data_manager = RealEstateDataManager(retriever)

# Define search parameters
search_params = {
    "city": "Genova",
    "zones": ["Centro", "Castelletto"],
    "price_min": 100000,
    "price_max": 300000,
    "size_min": 70
}

# Fetch and save ads
data_manager.fetch_and_save_ads(
    search_params,
    output_format="csv",
    filename="genova_apartments.csv"
)
```

Example usage - Machine Learning:
```python
from immob.api_immobiliare.preprocessing import create_preprocessing_pipeline
from immob.api_immobiliare.ml_utils import train_multiple_models, evaluate_model
import pandas as pd

# Load collected data
ads_df = pd.read_csv("genova_apartments.csv")

# Preprocess the data
pipeline = create_preprocessing_pipeline()
X = pipeline.fit_transform(ads_df)
y = ads_df['price']

# Split data and train models
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
models = train_multiple_models(X_train, y_train)

# Evaluate the best model
results = evaluate_model(models['random_forest'], X_test, y_test)
print(f"R² Score: {results['r2']}")
print(f"Mean Absolute Error: {results['mae']}")
```

For more detailed examples, see:
- `immob/api_immobiliare/auxiliary/real_estate_ml_example.py` - ML example
- `immob/api_immobiliare/README_ML.md` - ML documentation
- API documentation in the `docs/` folder

### Other Projects
- eBay scraper
- Vinted scraper
- Ryanair price monitor
- Movie downloader

## Requirements
Each project has its own requirements.txt file in its respective directory.
