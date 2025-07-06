real_estate_models
==================

The ``real_estate_models`` module contains Pydantic data models for representing real estate advertisements
with data validation and standardization.

.. automodule:: immob.api_immobiliare.real_estate_models
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Features
-----------

* Standardized data model for real estate ads using Pydantic
* Built-in data validation for property fields
* Type checking and field normalization
* Support for serialization and deserialization

Usage Example
------------

.. code-block:: python

   from immob.api_immobiliare.real_estate_models import RealEstateAd
   
   # Create a new real estate ad
   ad = RealEstateAd(
       id="123456",
       title="Modern apartment in city center",
       price=250000,
       size=85,
       rooms=3,
       bathrooms=2,
       floor=2,
       has_elevator=True,
       property_type="apartment",
       location="City Center",
       city="Genova",
       url="https://example.com/ad/123456"
   )
   
   # Access properties
   print(f"Price per square meter: {ad.price_per_sqm}")
   
   # Convert to dict or JSON
   ad_dict = ad.dict()
   ad_json = ad.json()
