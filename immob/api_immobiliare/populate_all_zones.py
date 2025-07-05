#!/usr/bin/env python3
# --- populate_all_zones.py ---

import json
import requests
import logging
import argparse
import time
import random
from pathlib import Path
from populate_zones import load_common_cities, save_common_cities, query_zone_data, process_zone_data

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default paths
COMMON_CITIES_FILE = Path(__file__).resolve().parent / "common_cities.json"

def populate_zones_for_city(city_key, city_info, max_level=3, delay_range=(1.0, 2.0)):
    """
    Populate zones for a specific city
    
    Args:
        city_key: Key of the city in common_cities dictionary
        city_info: Dictionary containing city information
        max_level: Maximum level of detail (3 = zones/neighborhoods)
        delay_range: Tuple of min/max delay between requests
        
    Returns:
        Updated city_info dictionary with zones
    """
    city_name = city_info.get("name")
    if not city_name:
        logger.warning(f"Missing name for city '{city_key}', skipping")
        return city_info
    
    logger.info(f"Populating zones for city: {city_name}")
    
    # Query API for zone data
    zone_data = query_zone_data(city_name, max_level, delay_range)
    
    if not zone_data:
        logger.warning(f"No zone data found for city: {city_name}")
        return city_info
    
    # Create a temporary dictionary to hold just this city
    temp_dict = {city_key: city_info}
    
    # Process zone data
    updated_dict = process_zone_data(zone_data, temp_dict)
    
    return updated_dict.get(city_key, city_info)

def populate_all_zones(max_level=3, delay_range=(1.0, 2.0)):
    """
    Populate zones for all cities in common_cities.json
    
    Args:
        max_level: Maximum level of detail (3 = zones/neighborhoods)
        delay_range: Tuple of min/max delay between requests
    
    Returns:
        Updated common_cities dictionary
    """
    # Load current common cities data
    common_cities = load_common_cities()
    
    # Backup the original data
    backup_file = f"{COMMON_CITIES_FILE}.backup"
    save_common_cities(common_cities, backup_file)
    logger.info(f"Created backup at {backup_file}")
    
    # Process each city
    for city_key, city_info in common_cities.items():
        # Skip if already has macrozones
        if "macrozones" in city_info and city_info["macrozones"]:
            logger.info(f"City '{city_info.get('name', city_key)}' already has macrozones, skipping")
            continue
        
        # Populate zones for this city
        updated_city_info = populate_zones_for_city(city_key, city_info, max_level, delay_range)
        
        # Update the dictionary
        common_cities[city_key] = updated_city_info
        
        # Save after each city to avoid losing data if something goes wrong
        save_common_cities(common_cities)
        
        # Add a delay between cities to avoid rate limiting
        time.sleep(random.uniform(delay_range[0] * 2, delay_range[1] * 2))
    
    # Final save
    if save_common_cities(common_cities):
        logger.info("Successfully updated common_cities.json with zone data for all cities")
    else:
        logger.error("Failed to save updated zone data")
    
    return common_cities

def populate_zones_for_specific_cities(city_names, max_level=3, delay_range=(1.0, 2.0)):
    """
    Populate zones for specific cities by name
    
    Args:
        city_names: List of city names to populate zones for
        max_level: Maximum level of detail (3 = zones/neighborhoods)
        delay_range: Tuple of min/max delay between requests
    
    Returns:
        Updated common_cities dictionary
    """
    # Load current common cities data
    common_cities = load_common_cities()
    
    # Backup the original data
    backup_file = f"{COMMON_CITIES_FILE}.backup"
    save_common_cities(common_cities, backup_file)
    logger.info(f"Created backup at {backup_file}")
    
    # Find cities by name
    for city_name in city_names:
        city_name_lower = city_name.lower()
        found = False
        
        # First try exact match on key
        if city_name_lower in common_cities:
            city_key = city_name_lower
            city_info = common_cities[city_key]
            found = True
        else:
            # Try matching by name
            for key, info in common_cities.items():
                if info.get("name", "").lower() == city_name_lower:
                    city_key = key
                    city_info = info
                    found = True
                    break
        
        if found:
            logger.info(f"Found city: {city_info.get('name')} (key: {city_key})")
            
            # Populate zones for this city
            updated_city_info = populate_zones_for_city(city_key, city_info, max_level, delay_range)
            
            # Update the dictionary
            common_cities[city_key] = updated_city_info
            
            # Save after each city to avoid losing data if something goes wrong
            save_common_cities(common_cities)
            
            # Add a delay between cities to avoid rate limiting
            time.sleep(random.uniform(delay_range[0] * 2, delay_range[1] * 2))
        else:
            logger.warning(f"City not found: {city_name}")
    
    # Final save
    if save_common_cities(common_cities):
        logger.info("Successfully updated common_cities.json with zone data for specified cities")
    else:
        logger.error("Failed to save updated zone data")
    
    return common_cities

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Populate all zones in common_cities.json from Immobiliare.it API')
    parser.add_argument('--all', action='store_true', help='Populate zones for all cities in the common_cities.json file')
    parser.add_argument('--cities', nargs='*', help='Names of specific cities to populate zones for')
    parser.add_argument('--max-level', type=int, default=3, help='Maximum level of detail (default: 3 = zones/neighborhoods)')
    parser.add_argument('--min-delay', type=float, default=1.0, help='Minimum delay between requests in seconds (default: 1.0)')
    parser.add_argument('--max-delay', type=float, default=2.0, help='Maximum delay between requests in seconds (default: 2.0)')
    parser.add_argument('--file', type=str, default=str(COMMON_CITIES_FILE), help=f'Path to common_cities.json file (default: {COMMON_CITIES_FILE})')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # Set file path if provided
    global COMMON_CITIES_FILE
    if args.file:
        COMMON_CITIES_FILE = Path(args.file)
    
    if args.all:
        # Populate zones for all cities
        populate_all_zones(
            max_level=args.max_level,
            delay_range=(args.min_delay, args.max_delay)
        )
    elif args.cities:
        # Populate zones for specific cities
        populate_zones_for_specific_cities(
            city_names=args.cities,
            max_level=args.max_level,
            delay_range=(args.min_delay, args.max_delay)
        )
    else:
        logger.error("Please specify either --all or --cities")

if __name__ == "__main__":
    main()
