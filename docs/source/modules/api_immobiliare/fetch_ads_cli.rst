fetch_ads_cli
=============

The ``fetch_ads_cli`` module provides a command-line interface for fetching real estate ads using the API Immobiliare framework.

.. automodule:: immob.api_immobiliare.fetch_ads_cli
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* Command-line interface for ad retrieval
* Support for various command-line arguments
* Integration with the data manager and retriever classes
* Configurable output formats and parameters

Usage
-----

.. code-block:: bash

   # Basic usage
   python -m immob.api_immobiliare.fetch_ads_cli --city Genova --output-format csv
   
   # Specify zones
   python -m immob.api_immobiliare.fetch_ads_cli --city Roma --zones "Centro,Prati,Trastevere" --output-format json
   
   # Set price range
   python -m immob.api_immobiliare.fetch_ads_cli --city Milano --price-min 200000 --price-max 500000 --output-format sqlite
   
   # Full example with multiple parameters
   python -m immob.api_immobiliare.fetch_ads_cli \
       --city Torino \
       --zones "Centro,Crocetta" \
       --property-type apartment \
       --transaction-type sell \
       --price-min 150000 \
       --price-max 350000 \
       --size-min 70 \
       --rooms-min 2 \
       --output-format csv \
       --output-file "torino_apartments.csv" \
       --log-level INFO
