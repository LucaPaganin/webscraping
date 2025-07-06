#!/usr/bin/env python3
"""
Real Estate Data Collection Package
===================================

A comprehensive, object-oriented system for retrieving real estate data from various websites.
Currently supports immobiliare.it with extensible architecture for additional sources.

Author: Lucas P
Date: July 6, 2025
"""

from .real_estate_models import RealEstateAd
from .retrievers import RealEstateAdRetriever, ImmobiliareAdRetriever
from .data_manager import RealEstateDataManager
from .config import load_configuration, setup_logging, validate_configuration

__version__ = "1.0.0"
__author__ = "Lucas P"

__all__ = [
    "RealEstateAd",
    "RealEstateAdRetriever", 
    "ImmobiliareAdRetriever",
    "RealEstateDataManager",
    "load_configuration",
    "setup_logging",
    "validate_configuration"
]
