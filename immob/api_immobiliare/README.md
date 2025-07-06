# Real Estate Data Collection System (OOP)

A modern, object-oriented Python framework for collecting real estate data from various websites. Currently supports immobiliare.it with an extensible architecture for adding new sources.

## 🏗️ Architecture Overview

The system follows a clean, object-oriented design that separates concerns and provides extensibility:

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   RealEstateAd      │    │ RealEstateAdRetriever│    │ RealEstateDataManager│
│   (Pydantic Model) │    │   (Abstract Base)    │    │   (Coordinator)     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
           │                           │                           │
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │ ImmobiliareAdRetriever    │
                         │ (Concrete Implementation)│
                         └───────────────────────────┘
```

### Key Components

- **`RealEstateAd`**: Standardized Pydantic model for all ad data
- **`RealEstateAdRetriever`**: Abstract base class defining the contract for data retrieval
- **`ImmobiliareAdRetriever`**: Concrete implementation for immobiliare.it
- **`RealEstateDataManager`**: Orchestrates data collection and storage operations

## 🚀 Quick Start

### Installation

Install required packages:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project directory:

```env
# Azure Cosmos DB (optional)
COSMOS_ENDPOINT=your_cosmos_endpoint
COSMOS_KEY=your_cosmos_key
COSMOS_DATABASE=your_database_name

# API Configuration
IMMOBILIARE_BASE_URL=https://api.immobiliare.it/search
REQUEST_DELAY_MIN=2.5
REQUEST_DELAY_MAX=5.0
MAX_RETRIES=3

# Output Configuration
DEFAULT_OUTPUT_PATH=./data
```

### Basic Programmatic Usage

```python
from fetch_immobiliare_ads import ImmobiliareAdRetriever, RealEstateDataManager, load_configuration

# Load configuration
config = load_configuration()

# Create retriever and data manager
retriever = ImmobiliareAdRetriever(config)
data_manager = RealEstateDataManager(retriever, config)

# Collect ads for Genova (sale properties)
ads = data_manager.collect_ads(
    city='genova',
    contract_type='sale',
    max_pages=5
)

print(f"Collected {len(ads)} ads")
```

### Command Line Usage

```bash
# Fetch rental ads for Genova (1 page)
python fetch_immobiliare_ads.py --city genova --contract rent

# Fetch all sale ads for Genova, zone by zone
python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0 --use-zones --region lig

# List available zones for a city
python fetch_immobiliare_ads.py --city genova --list-zones

# Save to multiple formats
python fetch_immobiliare_ads.py --city genova --save-csv --save-json --save-sqlite
```

## 📊 Data Model

The `RealEstateAd` model standardizes data across all sources:

```python
@dataclass
class RealEstateAd:
    id: str                           # Unique identifier
    source_url: str                   # Original URL
    source_website: str               # Source website
    title: str                        # Property title
    contract_type: str                # 'rent' or 'sale'
    price: Optional[float] = None     # Price in EUR
    surface: Optional[int] = None     # Surface area (sqm)
    rooms: Optional[int] = None       # Number of rooms    address: Optional[str] = None     # Full address
    city: Optional[str] = None        # City name
    latitude: Optional[float] = None  # GPS latitude
    longitude: Optional[float] = None # GPS longitude
    features: List[str] = None        # Property features
    images: List[str] = None          # Image URLs
    # ... and more fields
```

## Command-Line Parameters

#### Location Parameters:
- `--city`, `-c`: City to search for ads (default: genova)
- `--region`: Region code for zone-based searching (e.g., 'lig' for Liguria)
- `--macrozones`: List of macrozone IDs to filter results (e.g., --macrozones 13297 13298)
- `--use-zones`: Process zones individually for comprehensive coverage
- `--list-zones`: List available zones for the selected city and exit

#### Contract and Pagination:
- `--contract`, `-t`: Contract type: rent or sale (default: rent)
- `--max-pages`, `-m`: Maximum number of pages to fetch (default: 1, 0 for all)
- `--start-page`: Page to start fetching from (default: 1)

#### Output Options:
- `--output-path`, `-o`: Directory to save output files (default: current directory)
- `--save-csv`: Save results to CSV format (default: True)
- `--no-save-csv`: Disable CSV output
- `--save-json`: Save results to JSON format
- `--save-sqlite`: Save results to SQLite database
- `--sqlite-path`: Custom path for SQLite database
- `--save-cosmos`: Save results to Azure Cosmos DB
- `--cosmos-container`: Custom Cosmos DB container name

#### Logging:
- `--log-to-file`: Save logs to a file

## 🎯 Key Features

### ✅ Extensible Architecture
- Easy to add new real estate websites
- Abstract base class ensures consistent interface
- Standardized data model across all sources

### ✅ Comprehensive Data Collection
- **Hierarchical Location Search**: City → Comune → Macrozone → Zone
- **Advanced Filtering**: Property type, contract type, price range
- **Pagination Support**: Automatic handling of multi-page results
- **Rate Limiting**: Configurable delays to respect website policies

### ✅ Multiple Storage Options
- **CSV**: For data analysis and Excel compatibility
- **JSON**: For web applications and APIs
- **SQLite**: For local database operations
- **Azure Cosmos DB**: For cloud-scale applications

### ✅ Advanced Feature Engineering
- **Text-Based Features**: Extract insights from property descriptions
- **Geographic Features**: Location-based insights and neighborhood analysis
- **Time-Based Features**: Temporal patterns and seasonality
- **Price Trend Analysis**: Historical price trends and market dynamics
- **Sentiment Analysis**: Property description sentiment evaluation
- **Energy Efficiency Features**: Energy class impact analysis
- **Neighborhood Clustering**: Automated micro-market identification
- **External Data Integration**: Census data, POIs, and other contextual information

### ✅ Model Building & Optimization
- **Model Registry**: Version control for trained models
- **Hyperparameter Optimization**: Automated model tuning
- **Feature Importance Analysis**: Identify key value drivers
- **Performance Evaluation**: Comprehensive metrics and analysis

### ✅ Robust Error Handling
- Retry logic with exponential backoff
- Graceful degradation on API failures
- Comprehensive logging and monitoring

### ✅ Developer-Friendly
- Type hints throughout the codebase
- Comprehensive docstrings
- Configurable via environment variables
- Command-line interface with extensive options

## 🧠 Advanced Feature Engineering

The system includes advanced feature engineering capabilities through two key modules:

### `advanced_features.py`

Provides basic feature extraction transformers:

- `DescriptionFeatureExtractor`: Extracts binary features from property descriptions
- `GeographicFeatureTransformer`: Creates features from geographic coordinates
- `TimeFeatureTransformer`: Generates features from date fields
- `TextVectorizerTransformer`: Converts descriptions to vector representations

### `enhanced_features.py`

Extends the basic transformers with more sophisticated feature engineering:

- `PriceTrendAnalyzer`: Analyzes historical price data to extract trends and volatility metrics
- `NeighborhoodClusterer`: Groups properties into micro-markets using unsupervised learning
- `SentimentAnalysisTransformer`: Performs sentiment analysis on property descriptions
- `EnergyEfficiencyTransformer`: Extracts and transforms energy efficiency information
- `ExternalDataEnricher`: Integrates external data sources like census data and POIs

### Example Usage

```python
from enhanced_features import (
    PriceTrendAnalyzer,
    NeighborhoodClusterer,
    create_enhanced_feature_pipeline
)

# Create individual transformers
price_analyzer = PriceTrendAnalyzer()
neighborhood_clusterer = NeighborhoodClusterer(n_clusters=10)

# Or use the complete pipeline
pipeline = create_enhanced_feature_pipeline(
    include_price_trends=True,
    include_neighborhoods=True,
    include_sentiment=True,
    include_energy=True,
    n_clusters=10
)

# Transform your data
enhanced_features = pipeline.fit_transform(df)
```

Check out the `examples/enhanced_feature_engineering.ipynb` notebook for comprehensive examples.

## 📊 Model Management

The system includes tools for model management and hyperparameter optimization:

### `model_utils.py`

- `ModelRegistry`: Manages trained models with version control and metadata
- `HyperparameterOptimizer`: Automates model tuning via grid search or randomized search

### Example Usage

```python
from model_utils import ModelRegistry, HyperparameterOptimizer

# Save a trained model
registry = ModelRegistry(registry_path='models')
model_id = registry.save_model(
    model=trained_model,
    model_name='price_prediction',
    feature_names=feature_names,
    metrics={'rmse': 50000, 'r2': 0.85}
)

# Load the best model
best_model_id = registry.get_best_model('price_prediction', metric='r2')
best_model, metadata = registry.load_model(best_model_id)

# Optimize hyperparameters
optimizer = HyperparameterOptimizer(
    pipeline=model_pipeline,
    param_grid=param_grid
)
results = optimizer.randomized_search(X_train, y_train)
```

## 🏢 Adding New Real Estate Websites

To add support for a new website, create a new retriever class:

```python
class NewWebsiteAdRetriever(RealEstateAdRetriever):
    """Retriever for newwebsite.com"""
    
    def get_city_zones(self, city: str) -> Dict[str, Any]:
        """Get available zones for the city from newwebsite.com API"""
        # Implementation specific to new website
        pass
    
    def build_search_params(self, **kwargs) -> Dict[str, Any]:
        """Build search parameters for newwebsite.com API"""
        # Implementation specific to new website
        pass
    
    def fetch_page(self, params: Dict, page: int) -> Tuple[List[Dict], bool]:
        """Fetch a single page from newwebsite.com"""
        # Implementation specific to new website
        pass
    
    def parse_ad(self, raw_ad: Dict) -> RealEstateAd:
        """Parse raw ad data to standardized RealEstateAd model"""
        # Implementation specific to new website
        pass
```

Then use it with the same data manager:

```python
# Create new retriever
new_retriever = NewWebsiteAdRetriever(config)
data_manager = RealEstateDataManager(new_retriever, config)

# Same interface for data collection!
ads = data_manager.collect_ads(city='milan', contract_type='rent')
```

## 🔧 Advanced Usage Examples

### Zone-based Collection with Custom Output

```python
# Collect ads for all zones in Genova
ads_by_zone = retriever.fetch_by_zones(
    city='genova',
    contract_type='sale',
    max_pages=10
)

# Save each zone separately
for zone_name, zone_ads in ads_by_zone.items():
    filename = f"genova_sale_{zone_name}.csv"
    data_manager.save_to_csv(zone_ads, filename)
```

### Custom Filtering and Processing

```python
# Collect ads with custom filters
ads = data_manager.collect_ads(
    city='genova',
    contract_type='rent',
    max_pages=0,  # All pages
    use_zones=True,
    macrozones=['13297', '13298']  # Specific neighborhoods
)

# Filter by price range
affordable_ads = [
    ad for ad in ads 
    if ad.price and ad.price <= 1000
]

# Save filtered results
data_manager.save_to_json(affordable_ads, 'affordable_rentals.json')
```

### Feature Engineering and Model Training

```python
import pandas as pd
from enhanced_features import create_enhanced_feature_pipeline
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Load collected data
ads_df = pd.DataFrame([ad.__dict__ for ad in ads])

# Create feature pipeline
pipeline = create_enhanced_feature_pipeline(
    include_price_trends=True,
    include_neighborhoods=True,
    include_sentiment=True
)

# Generate features
features = pipeline.fit_transform(ads_df)

# Train a model
X = features
y = ads_df['price']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestRegressor(n_estimators=100)
model.fit(X_train, y_train)

# Save model using the registry
from model_utils import ModelRegistry
registry = ModelRegistry()
registry.save_model(model, 'price_prediction', X.columns.tolist(), 
                   {'r2': model.score(X_test, y_test)})
```

### Batch Processing Multiple Cities

```python
cities = ['genova', 'milano', 'torino']
all_ads = []

for city in cities:
    city_ads = data_manager.collect_ads(
        city=city,
        contract_type='sale',
        max_pages=5
    )
    all_ads.extend(city_ads)

# Save combined results
data_manager.save_to_sqlite(all_ads, 'northern_italy_sales.db')
```

## 📈 Performance Considerations

- **Rate Limiting**: Default 2.5-5 second delays between requests
- **Connection Pooling**: Uses `requests.Session` for efficient connections
- **Memory Management**: Processes data in chunks for large datasets
- **Error Recovery**: Automatic retries with exponential backoff

## 🛡️ Security Features

- **Environment Variables**: No hardcoded credentials
- **Secure Headers**: Proper User-Agent and request headers
- **Rate Limiting**: Respects website policies
- **Error Sanitization**: Sensitive data not logged

## 📚 Dependencies

```txt
requests>=2.31.0
pandas>=2.0.0
pydantic>=2.0.0
azure-cosmos>=4.5.0
python-dotenv>=1.0.0
scikit-learn>=1.0.0
matplotlib>=3.5.0
seaborn>=0.12.0
joblib>=1.1.0
```

## 🔮 Future Roadmap

- [ ] Support for additional websites (Casa.it, Subito.it)
- [ ] Advanced filtering options (price ranges, property features)
- [ ] Real-time monitoring and change detection
- [x] Machine learning integration for price prediction
- [ ] REST API for data access
- [ ] Parallel processing for faster data collection
- [ ] Data quality validation and enrichment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-website`
3. Implement your retriever class following the abstract base class
4. Add tests for your implementation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with ❤️ for the real estate data community*
