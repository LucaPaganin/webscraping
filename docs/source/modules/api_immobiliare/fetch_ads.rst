fetch_ads Module
=============

.. py:module:: immob.api_immobiliare.fetch_ads

The ``fetch_ads`` module provides functionality for fetching real estate ads from immobiliare.it.
It's a simpler alternative to the more comprehensive ``fetch_immobiliare_ads`` module.

Module Summary
-------------

This module offers a straightforward approach to scraping immobiliare.it:

- Simplified command-line interface
- Basic fetching of rental and sale properties
- Support for saving to JSON and CSV formats
- City and contract type filtering

Key Functions
------------

.. py:function:: fetch_ads(city, contract_type, max_pages=1)
   
   Fetch real estate ads for a specific city and contract type.
   
   :param str city: City name
   :param str contract_type: 'rent' or 'sale'
   :param int max_pages: Maximum number of pages to fetch (default: 1)
   :return: DataFrame containing the fetched ads
   :rtype: pandas.DataFrame

.. py:function:: save_ads(df, output_file, format='csv')
   
   Save ads DataFrame to a file.
   
   :param pandas.DataFrame df: DataFrame with ad data
   :param str output_file: Output file path
   :param str format: Output format ('csv' or 'json')
   :return: True if successful, False otherwise
   :rtype: bool

Command-line Interface
---------------------

.. code-block:: text

    usage: fetch_ads.py [-h] [--city CITY] [--contract {rent,sale}]
                      [--max-pages MAX_PAGES] [--save-json] [--output OUTPUT]

Usage Examples
-------------

.. code-block:: bash

    # Fetch 1 page of rental ads for Genova
    python fetch_ads.py --city genova --contract rent
    
    # Fetch all sale ads for Genova and save to JSON
    python fetch_ads.py --city genova --contract sale --max-pages -1 --save-json

Configuration
------------

The module supports basic configuration options:

- **City**: Specify the city to search for ads
- **Contract Type**: Choose between 'rent' and 'sale'
- **Max Pages**: Control the number of pages to fetch
- **Output Format**: Save as CSV or JSON

Dependencies
-----------

- requests: For HTTP requests
- pandas: For data manipulation
- argparse: For command-line interface
