Data Upload Utilities
===================

The API Immobiliare package includes a unified data upload tool that leverages the
``RealEstateDataManager`` to upload data from CSV files to various storage destinations.

.. automodule:: immob.api_immobiliare.upload_data
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* Upload CSV files to multiple destinations (SQLite, Cosmos DB, JSON, CSV)
* Batch processing to handle large files
* Automatic metadata extraction from filenames
* Detailed reporting and error tracking
* Support for processing multiple files and directories

Usage Example
------------

.. code-block:: python

   from immob.api_immobiliare.upload_data import upload_csv_with_batches
   from immob.api_immobiliare.data_manager import RealEstateDataManager
   from immob.api_immobiliare.retrievers import RealEstateAdRetriever
   from immob.api_immobiliare.config import load_configuration
   
   # Initialize components
   config = load_configuration()
   retriever = RealEstateAdRetriever.create_mock_retriever(config)
   data_manager = RealEstateDataManager(retriever, config)
   
   # Upload CSV data to SQLite with batch processing
   result = upload_csv_with_batches(
       csv_path="data/milano_apartments.csv",
       data_manager=data_manager,
       output_format="sqlite",
       batch_size=50,
       db_path="real_estate.db",
       table_name="milano_ads"
   )
   
   print(f"Upload complete: {result['successful']}/{result['total_records']} records successful")

Command-Line Usage
-----------------

The upload tool can also be used directly from the command line:

.. code-block:: bash

   # Upload to SQLite database
   python -m immob.api_immobiliare.upload_data data/*.csv --sqlite real_estate.db
   
   # Upload to Cosmos DB
   python -m immob.api_immobiliare.upload_data data/*.csv --cosmos --container ads
   
   # Save to JSON files
   python -m immob.api_immobiliare.upload_data data/*.csv --json --output-dir output/
