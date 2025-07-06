fetch_immobiliare_ads Module
==========================

.. py:module:: immob.api_immobiliare.fetch_immobiliare_ads

The ``fetch_immobiliare_ads`` module is a comprehensive tool for scraping real estate listings from immobiliare.it.
It provides both single-query and zone-by-zone processing capabilities.

Module Summary
-------------

This module is the primary tool for collecting real estate data from immobiliare.it. It offers:

- Configurable scraping for both rental and sale properties
- Zone-based processing for detailed neighborhood analysis
- Support for filtering by macrozones
- Multiple output formats (CSV, JSON, SQLite, Cosmos DB)
- Rate limiting and request management for stable operation
- Comprehensive logging and error handling

Key Functions
------------

.. py:function:: fetch_ads(area_params, base_url, headers=None, cookies=None, max_pages=None, start_page=1, delay_range=(2.5, 5.0))
   
   Core function that fetches real estate ads based on the provided parameters.
   
   :param dict area_params: Dictionary of parameters for the API
   :param str base_url: Base URL for the API
   :param dict headers: Optional dictionary of HTTP headers
   :param dict cookies: Optional dictionary of cookies
   :param int max_pages: Optional maximum number of pages to fetch (None for all)
   :param int start_page: Optional page to start fetching from (default: 1)
   :param tuple delay_range: Optional tuple of min/max delay between requests
   :return: DataFrame containing the fetched ads
   :rtype: pandas.DataFrame

.. py:function:: process_single_query(city, config)
   
   Process ads for a city with optional macrozones filter.
   
   :param str city: City name
   :param dict config: Configuration dictionary with various settings
   :return: DataFrame with fetched data
   :rtype: pandas.DataFrame

.. py:function:: process_all_zones(city, config)
   
   Process ads for all zones in a city, one by one.
   
   :param str city: City name
   :param dict config: Configuration dictionary with various settings
   :return: Dictionary with results summary
   :rtype: dict

.. py:function:: get_params_mapper(contract_type, comune_id=None, comune_name=None, macrozones=None, region=None)
   
   Get parameters mapper for different cities based on contract type.
   
   :param str contract_type: 'rent' or 'sale'
   :param str comune_id: Optional idComune parameter
   :param str comune_name: Optional name of the comune
   :param list macrozones: Optional list of macrozone IDs to filter
   :param str region: Optional region code (e.g., 'lig' for Liguria)
   :return: Dictionary mapping city names to API parameters
   :rtype: dict

Command-line Interface
---------------------

The module provides a comprehensive command-line interface:

.. code-block:: text

    usage: fetch_immobiliare_ads.py [-h] [--city CITY] [--contract {rent,sale}]
                                  [--max-pages MAX_PAGES] [--start-page START_PAGE]
                                  [--output-path OUTPUT_PATH] [--log-to-file]
                                  [--comune-query COMUNE_QUERY] [--comune-id COMUNE_ID]
                                  [--comune-name COMUNE_NAME] [--region REGION]
                                  [--use-zones] [--list-zones]
                                  [--macrozones MACROZONES [MACROZONES ...]]
                                  [--macrozone-names MACROZONE_NAMES [MACROZONE_NAMES ...]]
                                  [--no-combined-results] [--save-csv] [--no-save-csv]
                                  [--save-json] [--save-sqlite] [--sqlite-path SQLITE_PATH]
                                  [--save-cosmos]

Usage Examples
-------------

.. code-block:: bash

    # List available zones for Genova
    python fetch_immobiliare_ads.py --city genova --list-zones
    
    # Fetch all sale ads for Genova, zone by zone
    python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0 --use-zones --region lig
    
    # Fetch ads only for specific macrozones using names
    python fetch_immobiliare_ads.py --city genova --macrozone-names centro foce

Configuration
------------

The module supports various configuration options:

- **Contract Type**: Choose between 'rent' and 'sale'
- **City**: Specify the city to search for ads
- **Zones**: Option to process zones individually
- **Macrozones**: Filter by specific macrozones
- **Output Path**: Where to save the output files
- **Storage Options**: Save to CSV, JSON, SQLite, or Cosmos DB
- **Pagination**: Control the number of pages to fetch
- **Logging**: Option to log to a file

Dependencies
-----------

- requests: For HTTP requests
- pandas: For data manipulation
- dotenv: For environment variables
- datetime: For timestamp generation
- argparse: For command-line interface
- helpers: For utility functions and models
- sqlite_helpers: For SQLite database operations
