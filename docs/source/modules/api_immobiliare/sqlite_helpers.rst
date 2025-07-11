sqlite_helpers Module
=================

.. py:module:: immob.api_immobiliare.sqlite_helpers

The ``sqlite_helpers`` module provides functions for working with SQLite databases
to store and retrieve real estate data.

Module Summary
-------------

This module offers:

- Database initialization and schema creation
- Efficient writing of DataFrames to SQLite
- Batch processing for large datasets
- Transaction management for data integrity

Key Functions
------------

.. py:function:: init_database(db_path, tables_config=None)
   
   Initialize SQLite database with required tables.
   
   :param str db_path: Path to SQLite database file
   :param dict tables_config: Optional configuration for tables to create
   :return: SQLite connection object
   :rtype: sqlite3.Connection

.. py:function:: write_df_to_sqlite(df, table_name, db_path, if_exists='append', index=False, batch_size=100)
   
   Write a DataFrame to a SQLite database table with batching.
   
   :param pandas.DataFrame df: DataFrame to write
   :param str table_name: Target table name
   :param str db_path: Path to SQLite database file
   :param str if_exists: What to do if table exists ('fail', 'replace', 'append')
   :param bool index: Whether to write DataFrame index
   :param int batch_size: Number of rows per batch
   :return: Dictionary with operation results
   :rtype: dict

.. py:function:: create_ads_table(connection)
   
   Create the main real estate ads table with all required fields.
   
   :param sqlite3.Connection connection: SQLite connection
   :return: True if successful, False otherwise
   :rtype: bool

.. py:function:: create_zones_table(connection)
   
   Create table for storing zone/neighborhood information.
   
   :param sqlite3.Connection connection: SQLite connection
   :return: True if successful, False otherwise
   :rtype: bool

Table Schemas
------------

The module defines several table schemas:

.. code-block:: sql

    -- Main ads table
    CREATE TABLE IF NOT EXISTS ads (
        id TEXT PRIMARY KEY,
        title TEXT,
        url TEXT,
        price REAL,
        price_formatted TEXT,
        surface INTEGER,
        rooms INTEGER,
        bathrooms INTEGER,
        lat REAL,
        lon REAL,
        address TEXT,
        comune TEXT,
        province TEXT,
        region TEXT,
        zone TEXT,
        zone_id INTEGER,
        description TEXT,
        contract_type TEXT,
        property_type TEXT,
        energy_class TEXT,
        condition TEXT,
        floor TEXT,
        elevator INTEGER,
        balcony INTEGER,
        terrace INTEGER,
        garden INTEGER,
        air_conditioning INTEGER,
        heating TEXT,
        date_created TEXT,
        date_scraped TEXT,
        features TEXT
    )

    -- Zones table
    CREATE TABLE IF NOT EXISTS zones (
        id INTEGER PRIMARY KEY,
        name TEXT,
        comune TEXT,
        comune_id TEXT,
        region TEXT,
        lat REAL,
        lon REAL
    )

Utility Functions
----------------

.. py:function:: get_record_count(db_path, table_name)
   
   Get the number of records in a table.
   
   :param str db_path: Path to SQLite database file
   :param str table_name: Table name to count records from
   :return: Number of records
   :rtype: int

.. py:function:: execute_query(db_path, query, params=None, fetch_mode='all')
   
   Execute a SQL query on the database.
   
   :param str db_path: Path to SQLite database file
   :param str query: SQL query to execute
   :param tuple params: Optional parameters for the query
   :param str fetch_mode: Fetch mode ('all', 'one', 'none')
   :return: Query results or None
   :rtype: list or dict or None

Dependencies
-----------

- sqlite3: For SQLite database operations
- pandas: For DataFrame handling
- datetime: For timestamp generation
- logging: For operation logging
