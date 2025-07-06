ml_utils
========

The ``ml_utils`` module provides machine learning utilities for real estate data analysis including model
training, evaluation, and feature selection methods.

.. automodule:: immob.api_immobiliare.ml_utils
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Features
-----------

* Functions to train multiple regression models simultaneously
* Model evaluation utilities with comprehensive metrics
* Feature importance analysis and selection
* Visualization tools for model performance
* Cross-validation and hyperparameter tuning helpers

Usage Example
------------

.. code-block:: python

   from immob.api_immobiliare.ml_utils import (
       train_multiple_models,
       evaluate_model,
       select_features_by_importance
   )
   import pandas as pd
   
   # Load your prepared dataset
   X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
   
   # Train multiple models at once
   models_dict = train_multiple_models(X_train, y_train)
   
   # Evaluate model performance
   evaluation_results = evaluate_model(models_dict['random_forest'], X_test, y_test)
   
   # Select important features
   X_selected = select_features_by_importance(
       models_dict['random_forest'], 
       X_train, 
       num_features=10
   )
