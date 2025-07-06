API Immobiliare Modules
=====================

This section contains detailed documentation for the Python modules in the ``api_immobiliare`` folder,
which provide an **object-oriented framework** for collecting, analyzing, and storing real estate data 
from various websites. The system currently supports immobiliare.it with an extensible architecture 
for adding new sources.

.. toctree::
   :maxdepth: 2
   :caption: Core Modules:
   
   api_immobiliare/real_estate_models
   api_immobiliare/retrievers
   api_immobiliare/data_manager
   api_immobiliare/config
   api_immobiliare/fetch_ads_cli
   api_immobiliare/fetch_immobiliare_ads

.. toctree::
   :maxdepth: 2
   :caption: Analysis & ML Modules:
   
   api_immobiliare/preprocessing
   api_immobiliare/ml_utils
   api_immobiliare/analyze_real_estate_data

.. toctree::
   :maxdepth: 2
   :caption: Utility Modules:
   
   api_immobiliare/helpers
   api_immobiliare/models
   api_immobiliare/sqlite_helpers
   api_immobiliare/upload_data
   api_immobiliare/fetch_ads
   api_immobiliare/filter_utils

Architecture Overview
-------------------

The API Immobiliare system follows a modern, **object-oriented design** that separates concerns 
and provides maximum extensibility:

**Core Components:**

- **RealEstateAd Model**: Standardized Pydantic model for all real estate data
- **RealEstateAdRetriever (Abstract)**: Base class defining the contract for data retrieval
- **ImmobiliareAdRetriever (Concrete)**: Implementation for immobiliare.it
- **RealEstateDataManager**: Coordinator for data collection and storage operations

**Key Benefits:**

- **Extensible**: Easy to add new real estate websites
- **Standardized**: Consistent data model across all sources
- **Maintainable**: Clear separation of concerns with single responsibility principle
- **Flexible**: Multiple storage options (CSV, JSON, SQLite, Cosmos DB)

Pipeline Overview
----------------

The system provides a complete pipeline for real estate data processing:

1. **Data Collection**: Object-oriented retrieval from multiple sources
2. **Data Standardization**: Conversion to unified ``RealEstateAd`` model
3. **Data Processing**: Cleaning, transformation, and filtering
4. **Data Storage**: Flexible output to various formats and databases
5. **Data Analysis**: Market analysis and visualization tools

Key Features
-----------

### 🏗️ Object-Oriented Architecture
- Abstract base classes for easy extension
- Composition pattern for flexible data management
- SOLID principles throughout the design

### 🌍 Multi-Source Support
- Currently supports immobiliare.it
- Extensible framework for additional websites
- Standardized data model across all sources

### 🔍 Advanced Data Collection
- **Hierarchical Location Search**: City → Comune → Macrozone → Zone
- **Smart Pagination**: Automatic handling of multi-page results
- **Rate Limiting**: Configurable delays to respect website policies
- **Error Recovery**: Robust retry logic with exponential backoff

### 💾 Flexible Storage Options
- **CSV**: For data analysis and Excel compatibility
- **JSON**: For web applications and APIs
- **SQLite**: For local database operations
- **Azure Cosmos DB**: For cloud-scale applications

### 📊 Comprehensive Analysis
- Real estate market analysis tools
- Price trend analysis
- Geographic data visualization
- Statistical reporting capabilities

### 🛡️ Enterprise-Ready Features
- Environment variable configuration
- Comprehensive logging and monitoring
- Type hints and validation throughout
- Azure integration following best practices
