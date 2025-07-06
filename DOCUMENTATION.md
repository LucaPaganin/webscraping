# Documentation Generation Guide

This project uses Sphinx to generate comprehensive documentation for all modules and scripts.

## Setting Up the Documentation Environment

1. Install the required documentation packages:

```bash
cd docs
pip install -r requirements.txt
```

2. Build the documentation:

```bash
# On Linux/Mac
cd docs
make html

# On Windows
cd docs
make.bat html
```

3. View the documentation:
   - Open `docs/build/html/index.html` in your browser

## Documentation Structure

- `docs/source/`: Contains the RST source files
- `docs/source/modules/`: Contains documentation for each module
- `docs/build/`: Contains the generated HTML documentation

## Adding New Documentation

To document a new module:

1. Create a new `.rst` file in `docs/source/modules/`
2. Add the module to the toctree in `docs/source/index.rst`
3. Use the Sphinx autodoc directives to include documentation from your code
4. Rebuild the documentation

## Best Practices for Code Documentation

- Use Google-style docstrings for all functions, classes, and methods
- Include parameter types and return types in docstrings
- Document exceptions that may be raised
- Provide usage examples where appropriate
- Keep docstrings up to date when changing code

Example of a well-documented function:

```python
def fetch_ads(area_params, base_url, headers=None, cookies=None, max_pages=None):
    """
    Fetch real estate ads from immobiliare.it based on the provided parameters.
    
    Args:
        area_params (dict): Dictionary of parameters for the API
        base_url (str): Base URL for the API
        headers (dict, optional): Dictionary of HTTP headers
        cookies (dict, optional): Dictionary of cookies
        max_pages (int, optional): Maximum number of pages to fetch
        
    Returns:
        pandas.DataFrame: DataFrame containing the fetched ads
        
    Raises:
        RequestException: If the HTTP request fails
        ValueError: If the response format is invalid
    """
    # Function implementation
```

## Recent Major Updates

### OOP Refactoring (2024)

The `fetch_immobiliare_ads.py` module has been completely refactored to use an **Object-Oriented Programming (OOP)** paradigm, providing significant improvements:

#### New Architecture Components

- **`RealEstateAd`**: Standardized Pydantic model for all real estate data
- **`RealEstateAdRetriever`**: Abstract base class for data retrieval
- **`ImmobiliareAdRetriever`**: Concrete implementation for immobiliare.it
- **`RealEstateDataManager`**: Coordinator for data collection and storage

#### Key Benefits

- **Extensibility**: Easy to add support for new real estate websites
- **Maintainability**: Clear separation of concerns with SOLID principles
- **Standardization**: Unified data model across all sources
- **Reliability**: Robust error handling and retry mechanisms
- **Flexibility**: Multiple storage options (CSV, JSON, SQLite, Cosmos DB)

#### Documentation Updates

The documentation has been comprehensively updated to reflect the new OOP structure:

- Updated module docstrings with class hierarchies and relationships
- Added detailed API documentation for all new classes and methods
- Provided usage examples for both programmatic and CLI interfaces
- Created architectural diagrams and design pattern explanations
- Updated README with modern features and extension guidelines

#### Migration Guide

The new OOP system maintains backward compatibility for CLI usage while providing enhanced programmatic interfaces:

```python
# Old procedural approach (deprecated)
# Direct function calls with complex parameter handling

# New OOP approach (recommended)
from fetch_immobiliare_ads import ImmobiliareAdRetriever, RealEstateDataManager

retriever = ImmobiliareAdRetriever(config)
data_manager = RealEstateDataManager(retriever, config)
ads = data_manager.collect_ads(city='genova', contract_type='sale')
```
