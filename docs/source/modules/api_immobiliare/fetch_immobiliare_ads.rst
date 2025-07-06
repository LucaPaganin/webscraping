fetch_immobiliare_ads Module
==========================

.. py:module:: immob.api_immobiliare.fetch_immobiliare_ads

The ``fetch_immobiliare_ads`` module is a comprehensive, object-oriented system for retrieving 
real estate data from various websites. It provides an extensible architecture that currently 
supports immobiliare.it with the ability to easily add other real estate websites.

Module Overview
--------------

This module implements a modern, object-oriented design pattern that separates concerns:

- **Data Models**: Standardized Pydantic models for real estate ads
- **Data Retrievers**: Abstract base class with concrete implementations for each website
- **Data Managers**: Coordination of retrieval and storage operations
- **Extensibility**: Easy addition of new real estate websites

The architecture follows SOLID principles and provides a clean separation between data retrieval,
processing, and storage operations.

Core Classes
-----------

Data Model
^^^^^^^^^^

.. py:class:: RealEstateAd

   Standardized Pydantic model for real estate advertisements from any source.
   
   This model ensures data consistency across different websites and provides validation.
   
   **Key Fields:**
   
   - ``id`` (str): Unique identifier for the ad
   - ``source_url`` (str): Original URL of the advertisement  
   - ``source_website`` (str): Source website (e.g., 'immobiliare.it')
   - ``title`` (str): Property title/headline
   - ``contract_type`` (str): Contract type (rent/sale)
   - ``price`` (Optional[float]): Property price
   - ``surface`` (Optional[int]): Surface area in square meters
   - ``rooms`` (Optional[int]): Number of rooms
   - ``address`` (Optional[str]): Property address
   - ``latitude``, ``longitude`` (Optional[float]): Geographic coordinates
   - ``city``, ``comune``, ``province``, ``region`` (Optional[str]): Location hierarchy
   - ``zone``, ``zone_id`` (Optional[str]): Neighborhood information
   - ``features`` (List[str]): List of property features
   - ``images`` (List[str]): List of image URLs
   
   **Validation:**
   
   - Price values must be non-negative
   - Surface area and room counts must be positive
   - Coordinates must be within valid geographic ranges
   
   **Methods:**
   
   - ``to_dict()``: Convert to dictionary for database storage
   - ``calculate_price_per_sqm()``: Calculate price per square meter

Abstract Retriever
^^^^^^^^^^^^^^^^^^

.. py:class:: RealEstateAdRetriever

   Abstract base class defining the interface for real estate ad retrievers.
   
   This class establishes the contract that all website-specific retrievers must implement,
   ensuring consistency and extensibility.
   
   **Abstract Methods:**
   
   - ``get_city_zones(city: str) -> Dict[str, Any]``: Get available zones for a city
   - ``build_search_params(**kwargs) -> Dict[str, Any]``: Build API search parameters
   - ``fetch_page(params: Dict, page: int) -> Tuple[List[Dict], bool]``: Fetch single page
   - ``parse_ad(raw_ad: Dict) -> RealEstateAd``: Parse raw data to standardized model
   
   **Concrete Methods:**
   
   - ``fetch_ads(**search_params) -> List[RealEstateAd]``: Fetch all ads matching criteria
   - ``fetch_by_zones(city: str, **search_params) -> Dict[str, List[RealEstateAd]]``: Zone-based fetching

Immobiliare.it Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:class:: ImmobiliareAdRetriever

   Concrete implementation for immobiliare.it website.
   
   This class implements all abstract methods from ``RealEstateAdRetriever`` specifically
   for the immobiliare.it API and data format.
   
   **Features:**
   
   - Full support for immobiliare.it API parameters
   - Zone-based searching using comune and macrozone filters
   - Automatic pagination handling
   - Rate limiting and request management
   - Robust error handling and retry logic
   
   **API Integration:**
   
   - Uses immobiliare.it's search API endpoint
   - Supports both rental and sale properties
   - Handles complex filtering by location hierarchy
   - Manages authentication cookies and headers

Data Manager
^^^^^^^^^^^

.. py:class:: RealEstateDataManager

   Coordinator class for data operations using composition pattern.
   
   This class manages the entire data pipeline from retrieval to storage,
   using a ``RealEstateAdRetriever`` instance to fetch data.
   
   **Storage Methods:**
   
   - ``save_to_csv(ads: List[RealEstateAd], filename: str) -> bool``
   - ``save_to_json(ads: List[RealEstateAd], filename: str) -> bool``
   - ``save_to_sqlite(ads: List[RealEstateAd], db_path: str) -> bool``
   - ``save_to_cosmos_db(ads: List[RealEstateAd], container_name: str) -> bool``
   - ``save_ads(ads: List[RealEstateAd], output_config: Dict) -> Dict[str, bool]``
   
   **Collection Methods:**
   
   - ``collect_ads(**search_params) -> List[RealEstateAd]``: Main collection method

Key Features
-----------

Extensible Architecture
^^^^^^^^^^^^^^^^^^^^^^

The OOP design makes it easy to add support for new real estate websites:

1. Create a new class inheriting from ``RealEstateAdRetriever``
2. Implement the four abstract methods for the new website's API
3. Use the same ``RealEstateDataManager`` for data operations

Data Standardization
^^^^^^^^^^^^^^^^^^^

All websites are converted to the same ``RealEstateAd`` model, ensuring:

- Consistent data structure across all sources
- Unified storage format
- Simplified analysis and processing

Advanced Filtering
^^^^^^^^^^^^^^^^^

- **Hierarchical Location Filtering**: City → Comune → Macrozone → Zone
- **Property Type Filtering**: Apartment, house, commercial, etc.
- **Contract Type Filtering**: Rent vs. sale
- **Custom Parameter Support**: Website-specific advanced filters

Storage Flexibility
^^^^^^^^^^^^^^^^^^

Multiple storage options with consistent interface:

- **CSV**: For analysis in Excel, Pandas, etc.
- **JSON**: For web applications and APIs
- **SQLite**: For local database operations
- **Azure Cosmos DB**: For cloud-scale applications

Command-line Interface
---------------------

The module provides a comprehensive CLI with the same functionality as before:

.. code-block:: text

    usage: fetch_immobiliare_ads.py [-h] [--city CITY] [--contract {rent,sale}]
                                  [--max-pages MAX_PAGES] [--start-page START_PAGE]
                                  [--output-path OUTPUT_PATH] [--log-to-file]
                                  [--region REGION] [--use-zones] [--list-zones]
                                  [--macrozones MACROZONES [MACROZONES ...]]
                                  [--save-csv] [--no-save-csv] [--save-json]
                                  [--save-sqlite] [--sqlite-path SQLITE_PATH]
                                  [--save-cosmos] [--cosmos-container COSMOS_CONTAINER]

Usage Examples
-------------

Basic Usage
^^^^^^^^^^

.. code-block:: bash

    # Fetch rental ads for Genova (1 page)
    python fetch_immobiliare_ads.py --city genova --contract rent
    
    # Fetch all sale ads for Genova
    python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0

Zone-based Processing
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Fetch all sale ads for Genova, zone by zone
    python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0 --use-zones --region lig
    
    # List available zones for a city
    python fetch_immobiliare_ads.py --city genova --list-zones

Advanced Filtering
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Fetch ads only for specific macrozones
    python fetch_immobiliare_ads.py --city genova --macrozones 13297 13298
    
    # Save to multiple formats
    python fetch_immobiliare_ads.py --city genova --save-csv --save-json --save-sqlite --save-cosmos

Programmatic Usage
^^^^^^^^^^^^^^^^^

.. code-block:: python

    from immob.api_immobiliare.fetch_immobiliare_ads import (
        ImmobiliareAdRetriever, RealEstateDataManager, load_configuration
    )
    
    # Load configuration
    config = load_configuration()
    config['contract_type'] = 'sale'
    config['region'] = 'lig'
    
    # Create retriever and data manager
    retriever = ImmobiliareAdRetriever(config)
    data_manager = RealEstateDataManager(retriever, config)
    
    # Collect ads
    ads = data_manager.collect_ads(
        city='genova',
        contract_type='sale',
        max_pages=5,
        use_zones=True
    )
    
    # Save to multiple formats
    output_config = {
        'output_path': './data',
        'city': 'genova',
        'contract_type': 'sale',
        'save_to_csv': True,
        'save_to_json': True,
        'save_to_sqlite': True
    }
    
    results = data_manager.save_ads(ads, output_config)

Architecture Benefits
-------------------

**Maintainability**
  - Clear separation of concerns
  - Single responsibility principle
  - Easy to test individual components

**Extensibility**
  - Abstract base class for easy addition of new websites
  - Standardized data model for all sources
  - Pluggable storage backends

**Reliability**
  - Comprehensive error handling
  - Robust retry logic with exponential backoff
  - Graceful degradation on failures

**Performance**
  - Efficient pagination handling
  - Connection pooling via requests.Session
  - Configurable rate limiting

**Security**
  - Environment variable configuration
  - No hardcoded credentials
  - Secure cookie and header management

Future Extensions
----------------

The architecture is designed to easily support:

- **Additional Websites**: Subilito.it, Casa.it, etc.
- **Advanced Filtering**: Price ranges, property features, etc.
- **Real-time Monitoring**: Change detection and notifications
- **Machine Learning**: Price prediction and market analysis
- **API Services**: REST API for data access

Dependencies
-----------

- **Core**: ``requests``, ``pandas``, ``pydantic``
- **Storage**: ``azure-cosmos``, ``sqlite3``
- **Configuration**: ``python-dotenv``
- **CLI**: ``argparse``
- **Utilities**: ``pathlib``, ``datetime``, ``logging``
