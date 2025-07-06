config
======

The ``config`` module provides configuration utilities and helper functions for the API Immobiliare system.

.. automodule:: immob.api_immobiliare.config
   :members:
   :undoc-members:
   :show-inheritance:

Key Features
-----------

* Configuration loading from YAML files
* Environment variable integration
* Logging setup and configuration
* Global settings management

Usage Example
------------

.. code-block:: python

   from immob.api_immobiliare.config import (
       load_configuration,
       setup_logging,
       get_user_agent
   )
   
   # Load configuration from default or specified path
   config = load_configuration()
   
   # Setup logging
   logger = setup_logging(log_level="INFO")
   
   # Get a randomized user agent for web requests
   user_agent = get_user_agent()
   
   # Access configuration values
   api_key = config.get("api_key")
   default_city = config.get("default_city", "Genova")
