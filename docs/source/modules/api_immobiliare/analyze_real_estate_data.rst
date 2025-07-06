analyze_real_estate_data Module
===========================

.. py:module:: immob.api_immobiliare.analyze_real_estate_data

The ``analyze_real_estate_data`` module provides tools for analyzing real estate data
collected from immobiliare.it, generating insights, statistics, and visualizations.

Module Summary
-------------

This module offers:

- Statistical analysis of real estate prices
- Zone-based price comparisons
- Time trend analysis
- Property type distribution analysis
- Visualization capabilities
- Data export functions

Key Functions
------------

.. py:function:: load_data(file_path=None, db_path=None, query=None)
   
   Load real estate data from CSV file or SQLite database.
   
   :param str file_path: Optional path to CSV file
   :param str db_path: Optional path to SQLite database
   :param str query: Optional SQL query for database loading
   :return: DataFrame with real estate data
   :rtype: pandas.DataFrame

.. py:function:: calculate_price_statistics(df, groupby=None, percentiles=[0.25, 0.5, 0.75])
   
   Calculate price statistics, optionally grouped by a column.
   
   :param pandas.DataFrame df: DataFrame with real estate data
   :param str groupby: Optional column to group by (e.g., 'zone', 'comune')
   :param list percentiles: List of percentiles to calculate
   :return: DataFrame with price statistics
   :rtype: pandas.DataFrame

.. py:function:: plot_price_distribution(df, column='zone', limit=10, figsize=(12, 8))
   
   Plot price distribution by a categorical column.
   
   :param pandas.DataFrame df: DataFrame with real estate data
   :param str column: Column to group by for distribution
   :param int limit: Limit to top N categories
   :param tuple figsize: Figure size (width, height)
   :return: Matplotlib figure and axes
   :rtype: tuple

.. py:function:: generate_report(df, output_file=None)
   
   Generate a comprehensive analysis report.
   
   :param pandas.DataFrame df: DataFrame with real estate data
   :param str output_file: Optional file to save the report
   :return: Dictionary with analysis results
   :rtype: dict

Analysis Capabilities
-------------------

The module provides several types of analysis:

1. **Price Analysis**:
   - Average, median, min, max prices
   - Price per square meter calculations
   - Price percentiles
   - Price outlier detection

2. **Geographical Analysis**:
   - Price heat maps by zone
   - Zone comparisons
   - Geographical clustering

3. **Property Feature Analysis**:
   - Impact of features on price
   - Correlation between features and price
   - Feature importance ranking

4. **Time Trend Analysis**:
   - Price trends over time
   - Listing volume trends
   - Seasonal patterns

Visualization Types
-----------------

The module generates various visualizations:

- Box plots for price distributions
- Bar charts for zone comparisons
- Heat maps for correlation analysis
- Scatter plots for price vs. area
- Histograms for feature distributions
- Geo maps for spatial analysis

Dependencies
-----------

- pandas: For data manipulation
- numpy: For numerical operations
- matplotlib: For basic plotting
- seaborn: For statistical visualizations
- sqlite3: For database access
- sklearn: For advanced statistical analysis
- geopandas: For geographical visualizations
