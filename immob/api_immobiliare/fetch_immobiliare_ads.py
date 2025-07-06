#!/usr/bin/env python3
"""
Real Estate Data Retrieval System (Legacy Wrapper)
=================================================

This file is kept for backward compatibility. For new code, please import
from the modular structure:

- real_estate_models.py: Data models for real estate ads
- retrievers.py: Classes for retrieving real estate data
- data_manager.py: Classes for managing data operations
- config.py: Configuration and utility functions
- fetch_ads_cli.py: Command-line interface

Author: Lucas P
Date: July 6, 2025
"""

import os
import sys
import logging


def main():
    """
    Main entry point for the legacy script.
    
    This function provides backward compatibility by redirecting to the new modular implementation.
    """
    print("Note: This script is maintained for backward compatibility.")
    print("For new code, use the modular implementation in fetch_ads_cli.py")
    
    # Import and call the new implementation
    from fetch_ads_cli import main as new_main
    new_main()


if __name__ == "__main__":
    main()
