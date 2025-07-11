Immobiliare
===========

This module contains tools for scraping and analyzing real estate data from immobiliare.it.

fetch_immobiliare_ads.py
-----------------------

.. automodule:: immob.api_immobiliare.fetch_immobiliare_ads
   :members:
   :undoc-members:
   :show-inheritance:

The ``fetch_immobiliare_ads.py`` script is a unified tool for fetching real estate ads from immobiliare.it with optional zone-by-zone processing.

Key Features
^^^^^^^^^^^

* Fetch real estate ads for both rental and sale properties
* Process an entire city or zone-by-zone for more granular data
* Support for filtering by macrozones
* Multiple output formats: CSV, JSON, SQLite, and Cosmos DB
* Configurable pagination and request delays

Usage Examples
^^^^^^^^^^^^

List available zones for a city:

.. code-block:: bash

    python fetch_immobiliare_ads.py --city genova --list-zones

Fetch all sale ads for Genova, zone by zone:

.. code-block:: bash

    python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0 --use-zones --region lig

Fetch ads only for specific macrozones using names:

.. code-block:: bash

    python fetch_immobiliare_ads.py --city genova --macrozone-names centro foce

Save results to multiple formats:

.. code-block:: bash

    python fetch_immobiliare_ads.py --city genova --save-csv --save-json --save-sqlite --output-path ./data

API Reference
^^^^^^^^^^^

Main Functions
~~~~~~~~~~~~~

- ``fetch_ads(area_params, base_url, headers=None, cookies=None, max_pages=None, start_page=1, delay_range=(2.5, 5.0))`` - Core function that fetches real estate ads based on provided parameters
- ``process_single_query(city, config)`` - Process ads for a city with optional macrozones filter
- ``process_zone_ads(city, zone_name, zone_id, config)`` - Process ads for a specific zone
- ``process_all_zones(city, config)`` - Process ads for all zones in a city
- ``save_data(df, city, zone_name=None, zone_id=None, contract_type="rent", config=None)`` - Save data to various formats based on configuration

Utility Functions
~~~~~~~~~~~~~

- ``get_comune_id_by_name(query)`` - Retrieve the idComune for a given search query
- ``get_params_mapper(contract_type, comune_id=None, comune_name=None, macrozones=None, region=None)`` - Get parameters mapper for different cities based on contract type
- ``get_params_for_zone(contract_type, comune_info, zone_id)`` - Get parameters for a specific zone API call
- ``clean_dataframe_for_export(df)`` - Clean DataFrame by replacing NaN values with None and empty strings with None
