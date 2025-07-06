retrievers
==========

The ``retrievers`` module provides abstract and concrete classes for retrieving real estate ads
from various websites. It follows an extensible design pattern with a common interface.

.. automodule:: immob.api_immobiliare.retrievers
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Features
-----------

* Abstract base class (`RealEstateAdRetriever`) defining common interface
* Concrete implementation for immobiliare.it (`ImmobiliareAdRetriever`)
* Methods for parameter building, page fetching, and ad parsing
* Support for different search criteria and filters

Usage Example
------------

.. code-block:: python

   from immob.api_immobiliare.retrievers import ImmobiliareAdRetriever
   from immob.api_immobiliare.data_manager import RealEstateDataManager
   
   # Create a retriever for immobiliare.it
   retriever = ImmobiliareAdRetriever()
   
   # Set search parameters
   search_params = {
       "city": "Genova",
       "zones": ["Centro", "Castelletto"],
       "price_min": 100000,
       "price_max": 300000,
       "size_min": 70
   }
   
   # Fetch ads
   ads = retriever.get_ads(search_params)
   
   # Use with data manager
   data_manager = RealEstateDataManager(retriever)
   data_manager.fetch_and_save_ads(
       search_params,
       output_format="csv",
       filename="genova_apartments.csv"
   )
