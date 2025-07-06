filter_utils Module
==============

.. py:module:: immob.api_immobiliare.filter_utils

The ``filter_utils`` module provides utilities for filtering and cleaning real estate data.
It helps with data preprocessing, normalization, and filtering for analysis.

Module Summary
-------------

This module offers:

- Advanced filtering capabilities for real estate data
- Data normalization and cleaning functions
- Outlier detection and removal
- Feature extraction from text descriptions
- Custom query builders

Key Functions
------------

.. py:function:: filter_dataframe(df, filters=None)
   
   Apply a set of filters to a DataFrame.
   
   :param pandas.DataFrame df: DataFrame to filter
   :param dict filters: Dictionary of filter conditions
   :return: Filtered DataFrame
   :rtype: pandas.DataFrame

.. py:function:: detect_outliers(df, column, method='iqr', threshold=1.5)
   
   Detect outliers in a numerical column.
   
   :param pandas.DataFrame df: DataFrame to analyze
   :param str column: Column to check for outliers
   :param str method: Method to use ('iqr', 'zscore', or 'isolation_forest')
   :param float threshold: Threshold for outlier detection
   :return: Boolean Series indicating outliers
   :rtype: pandas.Series

.. py:function:: normalize_features(df, features_list)
   
   Normalize property features for consistent analysis.
   
   :param pandas.DataFrame df: DataFrame with real estate data
   :param list features_list: List of feature columns to normalize
   :return: DataFrame with normalized features
   :rtype: pandas.DataFrame

.. py:function:: extract_keywords_from_description(df, keyword_list=None)
   
   Extract keywords from property descriptions.
   
   :param pandas.DataFrame df: DataFrame with real estate data
   :param list keyword_list: List of keywords to extract
   :return: DataFrame with additional keyword columns
   :rtype: pandas.DataFrame

Filter Types
-----------

The module supports various filter types:

1. **Range Filters**: For numerical columns like price and surface area
2. **List Filters**: For categorical columns like property_type
3. **Text Filters**: For searching within text columns
4. **Geographical Filters**: For location-based filtering
5. **Compound Filters**: For complex conditions

Example Usage
------------

.. code-block:: python

    import pandas as pd
    from immob.api_immobiliare.filter_utils import filter_dataframe, detect_outliers
    
    # Load data
    df = pd.read_csv('real_estate_data.csv')
    
    # Define filters
    filters = {
        'price': {'min': 100000, 'max': 500000},
        'surface': {'min': 50},
        'zone': {'include': ['centro', 'foce']},
        'property_type': {'include': ['apartment']}
    }
    
    # Apply filters
    filtered_df = filter_dataframe(df, filters)
    
    # Remove price outliers
    outliers = detect_outliers(filtered_df, 'price')
    clean_df = filtered_df[~outliers]

Advanced Features
----------------

- **Custom SQL Query Generation**: Convert filter dictionaries to SQL WHERE clauses
- **Complex Filter Composition**: Combine multiple filter conditions with AND/OR logic
- **Performance Optimization**: Efficient filtering for large datasets
- **Filter Validation**: Input validation for filter parameters

Dependencies
-----------

- pandas: For DataFrame operations
- numpy: For numerical calculations
- sklearn: For advanced outlier detection
- re: For regular expressions in text extraction
