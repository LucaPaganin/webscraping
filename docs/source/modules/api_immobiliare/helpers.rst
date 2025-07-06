helpers Module
============

.. py:module:: immob.api_immobiliare.helpers

The ``helpers`` module provides utility functions and classes for working with real estate data.
It contains core functionality used by multiple modules in the API Immobiliare package.

Module Summary
-------------

This module offers:

- Data models for real estate ads
- Cosmos DB client initialization and operations
- Data transformation and validation utilities
- DataFrame creation and manipulation functions

Key Classes
----------

.. py:class:: RealEstateAd

   Pydantic model representing a real estate ad with comprehensive validation.
   
   :param str id: Unique identifier for the ad
   :param str title: Title of the ad
   :param str url: URL to the ad listing
   :param float price: Price of the property
   :param str price_formatted: Formatted price string
   :param int surface: Surface area in square meters
   :param int rooms: Number of rooms
   :param int bathrooms: Number of bathrooms
   :param float lat: Latitude coordinate
   :param float lon: Longitude coordinate
   :param str address: Property address
   :param str comune: Municipality name
   :param str province: Province abbreviation
   :param str region: Region name
   :param str zone: Zone/neighborhood name
   :param str description: Property description
   :param str contract_type: Type of contract ('rent' or 'sale')
   :param str property_type: Type of property
   :param str energy_class: Energy efficiency class
   :param str condition: Property condition
   :param str floor: Floor number
   :param bool elevator: Elevator availability
   :param bool balcony: Balcony availability
   :param bool terrace: Terrace availability
   :param bool garden: Garden availability
   :param bool air_conditioning: Air conditioning availability
   :param str heating: Type of heating system
   :param list images: List of image URLs
   :param list features: List of property features
   :param datetime date_created: Ad creation date
   :param datetime date_scraped: Date when the ad was scraped
   :param int zone_id: Zone identifier

Key Functions
------------

.. py:function:: init_cosmos_client(endpoint, key, database_name)
   
   Initialize an Azure Cosmos DB client.
   
   :param str endpoint: Cosmos DB endpoint URL
   :param str key: Cosmos DB access key
   :param str database_name: Database name
   :return: Tuple of (CosmosClient, Database)
   :rtype: tuple

.. py:function:: create_ads_dataframe(ads_list)
   
   Create a pandas DataFrame from a list of ads.
   
   :param list ads_list: List of dictionaries representing ads
   :return: DataFrame with properly structured ad data
   :rtype: pandas.DataFrame

.. py:function:: transform_df_dtypes(df)
   
   Transform DataFrame column data types to appropriate types.
   
   :param pandas.DataFrame df: DataFrame to transform
   :return: DataFrame with corrected data types
   :rtype: pandas.DataFrame

.. py:function:: extract_id_from_url(url)
   
   Extract the ad ID from an immobiliare.it URL.
   
   :param str url: URL to process
   :return: Extracted ID or None
   :rtype: str or None

Utility Functions
----------------

.. py:function:: clean_price(price_str)
   
   Clean and normalize price strings.
   
   :param str price_str: Price string to clean
   :return: Cleaned price string
   :rtype: str

.. py:function:: parse_date(date_str)
   
   Parse date strings from various formats.
   
   :param str date_str: Date string to parse
   :return: Parsed datetime object or None
   :rtype: datetime.datetime or None

Dependencies
-----------

- pydantic: For data validation with the RealEstateAd model
- pandas: For DataFrame operations
- azure.cosmos: For Cosmos DB operations
- datetime: For date parsing and handling
- re: For regular expressions used in data extraction
