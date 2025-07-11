models Module
============

.. py:module:: immob.api_immobiliare.models

The ``models`` module defines data structures and models for representing real estate data.
It provides well-structured, validated models that ensure data consistency across the application.

Module Summary
-------------

This module contains:

- Pydantic models for real estate data
- Validation rules for all property fields
- Type definitions and constraints
- Helper methods for model conversion and manipulation

Key Classes
----------

.. py:class:: PropertyFeature

   Represents a feature or amenity of a property.
   
   :param str name: Name of the feature
   :param str value: Value or description of the feature
   :param str category: Category of the feature (e.g., 'interior', 'exterior')

.. py:class:: Location

   Represents the geographic location of a property.
   
   :param float latitude: Latitude coordinate
   :param float longitude: Longitude coordinate
   :param str address: Full address
   :param str city: City name
   :param str province: Province name or code
   :param str region: Region name
   :param str zone: Neighborhood or zone name
   :param str zone_id: Zone identifier
   :param str microzone: Smaller subdivision of a zone

.. py:class:: Price

   Represents the pricing information of a property.
   
   :param float value: Numeric price value
   :param str currency: Currency code (default: 'EUR')
   :param str frequency: For rentals, frequency of payment (e.g., 'month', 'year')
   :param bool negotiable: Whether the price is negotiable
   :param float price_per_sqm: Price per square meter

.. py:class:: RealEstateAd

   Comprehensive model for a real estate advertisement.
   
   :param str id: Unique identifier for the ad
   :param str title: Title of the ad
   :param str url: URL to the ad listing
   :param Price price: Price information
   :param int surface: Surface area in square meters
   :param Location location: Location information
   :param str description: Property description
   :param str contract_type: Type of contract ('rent' or 'sale')
   :param str property_type: Type of property
   :param str energy_class: Energy efficiency class
   :param list features: List of PropertyFeature objects
   :param datetime created_at: Ad creation date
   :param datetime scraped_at: Date when the ad was scraped

Methods
-------

.. py:function:: RealEstateAd.to_dict()
   
   Convert the model to a dictionary suitable for database storage.
   
   :return: Dictionary representation of the ad
   :rtype: dict

.. py:function:: RealEstateAd.from_raw_data(raw_data)
   
   Create an instance from raw data scraped from immobiliare.it.
   
   :param dict raw_data: Raw data dictionary
   :return: Validated RealEstateAd instance
   :rtype: RealEstateAd

Validators and Constraints
-------------------------

The module includes various validators to ensure data integrity:

- Price value must be non-negative
- Surface area must be positive
- Coordinates must be within valid ranges
- Required fields are enforced
- Date fields are properly formatted

Dependencies
-----------

- pydantic: For data validation and model definition
- datetime: For date handling
- typing: For type hints
