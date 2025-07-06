preprocessing
=============

The ``preprocessing`` module contains utilities for preprocessing real estate data before machine learning analysis.
This includes custom transformers, feature standardization functions, and complete preprocessing pipelines.

.. automodule:: immob.api_immobiliare.preprocessing
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
   
Key Features
-----------

* Custom transformers for handling real estate specific data (floors, garages, etc.)
* Functions to normalize and standardize feature values
* Complete preprocessing pipelines that can be applied to datasets
* Integration with scikit-learn transformer API

Usage Example
------------

.. code-block:: python

   from immob.api_immobiliare.preprocessing import (
       create_preprocessing_pipeline, 
       FloorNormalizer, 
       GarageStandardizer
   )
   
   # Create a complete preprocessing pipeline
   pipeline = create_preprocessing_pipeline()
   
   # Apply pipeline to your data
   X_transformed = pipeline.fit_transform(X)
   
   # Or use individual components
   floor_normalizer = FloorNormalizer()
   normalized_floors = floor_normalizer.fit_transform(df[['floor']])
