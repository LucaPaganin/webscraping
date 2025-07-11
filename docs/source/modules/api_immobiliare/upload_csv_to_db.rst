upload_csv_to_db Module
====================

.. py:module:: immob.api_immobiliare.upload_csv_to_db

The ``upload_csv_to_db`` module provides functionality for uploading real estate data
from CSV files to both SQLite and Cosmos DB databases.

Module Summary
-------------

This module offers:

- Batch uploading of CSV data to databases
- Support for both SQLite and Azure Cosmos DB
- Progress reporting and error handling
- Data transformation and validation during upload

Key Functions
------------

.. py:function:: upload_to_cosmos_db(df, container_client, batch_size=100, progress_callback=None)
   
   Upload DataFrame records to Azure Cosmos DB.
   
   :param pandas.DataFrame df: DataFrame to upload
   :param azure.cosmos.ContainerProxy container_client: Cosmos DB container client
   :param int batch_size: Number of records per batch
   :param function progress_callback: Optional callback for progress reporting
   :return: Dictionary with operation results
   :rtype: dict

.. py:function:: upload_to_sqlite(df, db_path, table_name='ads', batch_size=100, progress_callback=None)
   
   Upload DataFrame records to SQLite database.
   
   :param pandas.DataFrame df: DataFrame to upload
   :param str db_path: Path to SQLite database file
   :param str table_name: Target table name
   :param int batch_size: Number of records per batch
   :param function progress_callback: Optional callback for progress reporting
   :return: Dictionary with operation results
   :rtype: dict

Command-line Interface
---------------------

.. code-block:: text

    usage: upload_csv_to_db.py [-h] [--file FILE] [--directory DIRECTORY]
                             [--city CITY] [--container CONTAINER]
                             [--batch-size BATCH_SIZE] [--report]
                             [--cosmos] [--sqlite SQLITE]

Usage Examples
-------------

.. code-block:: bash

    # Upload a single CSV file to Cosmos DB
    python upload_csv_to_db.py --file data/ads_genova_rent.csv --container ads_rent --cosmos
    
    # Upload all CSV files in a directory to SQLite
    python upload_csv_to_db.py --directory data/ --sqlite ./ads.db --batch-size 50 --report
    
    # Upload all CSV files for a specific city to both databases
    python upload_csv_to_db.py --directory data/ --city genova --container ads_sale --sqlite ./ads.db --cosmos

Data Processing
--------------

The module performs several transformations during upload:

1. Data type conversion (strings to appropriate types)
2. Handling of NULL values
3. JSON serialization for nested structures
4. Validation against database schema
5. Duplicate handling

Configuration
------------

The module supports various configuration options:

- **File/Directory**: Specify single file or directory with CSV files
- **City Filter**: Filter CSV files by city name
- **Container**: Cosmos DB container name
- **Batch Size**: Number of records per batch (for performance)
- **Report**: Generate detailed report after upload
- **Database Selection**: Choose SQLite, Cosmos DB, or both

Dependencies
-----------

- pandas: For DataFrame operations
- azure.cosmos: For Cosmos DB operations
- dotenv: For environment variable loading
- glob: For file pattern matching
- pathlib: For path manipulation
- tqdm: For progress bars
