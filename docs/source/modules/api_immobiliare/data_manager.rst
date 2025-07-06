data_manager
============

The ``data_manager`` module provides classes for managing real estate data collection and storage operations.

.. automodule:: immob.api_immobiliare.data_manager
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Features
-----------

* Central management of ad retrieval and storage
* Support for multiple output formats (CSV, JSON, SQLite, Cosmos DB)
* Configurable logging and error handling
* Progress tracking for long-running operations

Usage Example
------------

.. code-block:: python

   from immob.api_immobiliare.retrievers import ImmobiliareAdRetriever
   from immob.api_immobiliare.data_manager import RealEstateDataManager
   
   # Initialize with a retriever
   retriever = ImmobiliareAdRetriever()
   data_manager = RealEstateDataManager(retriever)
   
   # Define search parameters
   search_params = {
       "city": "Milano",
       "property_type": "apartment",
       "transaction_type": "sell",
       "price_max": 500000
   }
   
   # Fetch and save to CSV
   data_manager.fetch_and_save_ads(
       search_params, 
       output_format="csv",
       filename="milano_apartments.csv"
   )
   
   # Fetch and save to SQLite
   data_manager.fetch_and_save_ads(
       search_params, 
       output_format="sqlite",
       db_path="real_estate.db",
       table_name="milano_apartments"
   )
