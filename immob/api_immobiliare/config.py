#!/usr/bin/env python3
"""
Configuration and Utility Functions
===================================

Configuration loading and utility functions for the real estate data system.

Author: Lucas P
Date: July 6, 2025
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def setup_logging(use_file: bool = False) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        use_file: Whether to also log to a file
        
    Returns:
        Configured logger instance
    """
    handlers = [logging.StreamHandler()]
    
    if use_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"real_estate_scraper_{timestamp}.log"
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=handlers
    )
    
    # Suppress verbose logs from external libraries
    logging.getLogger("azure.cosmos").setLevel(logging.WARNING)
    logging.getLogger("pydantic").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def load_configuration() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Configuration dictionary with all settings
    """
    # Try to load .env file from the current directory
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    
    return {
        # Azure Cosmos DB configuration
        "cosmos_endpoint": os.environ.get("COSMOS_DB_ACCOUNT_URI", ""),
        "cosmos_key": os.environ.get("COSMOS_DB_ACCOUNT_KEY", ""),
        "cosmos_db": os.environ.get("COSMOS_DB_DATABASE_NAME", ""),
        
        # API configuration
        "base_url": os.environ.get(
            "IMMOBILIARE_API_URL", 
            "https://www.immobiliare.it/api-next/search-list/listings/"
        ),
        
        # HTTP headers for requests
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.immobiliare.it",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        },
        
        # Cookies for session management
        "cookies": {
            "PHPSESSID": os.environ.get("PHPSESSID", "e5686b96fbe172ee7cd72d2fee24712d"),
            "IMMSESSID": os.environ.get("IMMSESSID", "e463dc3c67fb3bbc2073da5b3b8fcfed"),
            "datadome": os.environ.get("DATADOME", "raRTHfOWVs3UHHI0mL8JHd28BnmNGvrwoW0YQoe1OGWN0396cfnXqNZrH0efDY3YacgoqDuIrgM200pQSPu_HDzKNaXsJwGE6B2_cz_TqXauGiR04B_nuZPm7RCwmRt7")
        },
        
        # Request configuration
        "request_delay_min": float(os.environ.get("REQUEST_DELAY_MIN", "2.5")),
        "request_delay_max": float(os.environ.get("REQUEST_DELAY_MAX", "5.0")),
        "max_retries": int(os.environ.get("MAX_RETRIES", "3")),
        
        # Output configuration
        "default_output_path": os.environ.get("DEFAULT_OUTPUT_PATH", "."),
    }


def validate_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ValueError: If required configuration is missing or invalid
    """
    validated_config = config.copy()
    
    # Validate required fields
    required_fields = ["base_url", "headers"]
    for field in required_fields:
        if not config.get(field):
            raise ValueError(f"Required configuration field missing: {field}")
    
    # Validate delay ranges
    delay_min = validated_config.get("request_delay_min", 2.5)
    delay_max = validated_config.get("request_delay_max", 5.0)
    
    if delay_min < 0 or delay_max < 0:
        raise ValueError("Request delays must be non-negative")
    
    if delay_min > delay_max:
        validated_config["request_delay_min"] = delay_max
        validated_config["request_delay_max"] = delay_min
    
    # Validate max retries
    max_retries = validated_config.get("max_retries", 3)
    if max_retries < 0:
        validated_config["max_retries"] = 0
    elif max_retries > 10:
        validated_config["max_retries"] = 10
    
    return validated_config


def get_output_filename(city: str, contract_type: str, zone_name: str = None, 
                       timestamp: str = None, extension: str = "csv") -> str:
    """
    Generate a standardized output filename.
    
    Args:
        city: City name
        contract_type: Contract type (rent/sale)
        zone_name: Optional zone name for zone-specific files
        timestamp: Optional timestamp string
        extension: File extension
        
    Returns:
        Formatted filename string
    """
    if not timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    parts = [city, contract_type]
    
    if zone_name:
        # Sanitize zone name for filename
        safe_zone_name = "".join(c for c in zone_name if c.isalnum() or c in "-_").lower()
        parts.append(safe_zone_name)
    
    parts.append(timestamp)
    
    filename = "_".join(parts)
    return f"{filename}.{extension}"


def create_output_directory(output_path: str) -> Path:
    """
    Create output directory if it doesn't exist.
    
    Args:
        output_path: Path to output directory
        
    Returns:
        Path object for the created directory
    """
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    return path
