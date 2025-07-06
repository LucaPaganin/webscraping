API Immobiliare Modules
=====================

This section contains detailed documentation for the Python modules in the ``api_immobiliare`` folder,
which provide tools for scraping, analyzing, and storing real estate data from immobiliare.it.

.. toctree::
   :maxdepth: 2
   :caption: API Immobiliare Modules:
   
   api_immobiliare/fetch_immobiliare_ads
   api_immobiliare/fetch_ads
   api_immobiliare/helpers
   api_immobiliare/models
   api_immobiliare/sqlite_helpers
   api_immobiliare/upload_csv_to_db
   api_immobiliare/analyze_real_estate_data
   api_immobiliare/filter_utils

Overview
--------

The API Immobiliare modules provide a complete pipeline for real estate data:

1. **Data Collection**: Scraping real estate listings from immobiliare.it
2. **Data Processing**: Cleaning, transforming, and analyzing the collected data
3. **Data Storage**: Saving data to various formats (CSV, JSON, SQLite, Cosmos DB)
4. **Data Analysis**: Tools for analyzing and visualizing real estate data

Key Features
-----------

- Zone-based scraping for detailed neighborhood analysis
- Support for both rental and sale properties
- Flexible data filtering and transformation
- Multiple storage options including local and cloud databases
- Real estate market analysis tools
