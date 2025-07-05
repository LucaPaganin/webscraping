#!/usr/bin/env python3
# --- populate_zones.py ---

import json
import requests
import logging
import argparse
import time
import random
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default paths
COMMON_CITIES_FILE = Path(__file__).resolve().parent / "common_cities.json"

def load_common_cities(file_path=COMMON_CITIES_FILE):
    """Load the current common cities data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} cities from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading common cities file: {e}")
        return {}

def save_common_cities(data, file_path=COMMON_CITIES_FILE):
    """Save updated common cities data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Saved {len(data)} cities to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving common cities file: {e}")
        return False

def query_zone_data(query, max_level=3, delay_range=(1.0, 2.0)):
    """
    Query the Immobiliare.it autocomplete API for zone data
    
    Args:
        query: Search query for zones/neighborhoods
        max_level: Maximum level of detail (3 = zones/neighborhoods)
        delay_range: Tuple of min/max delay between requests
        
    Returns:
        List of zone data entries if successful, empty list otherwise
    """
    # Sanitize query
    query = query.replace(' ', '%20')
    
    url = f"https://www.immobiliare.it/api-next/geography/autocomplete/?query=\"{query}\"&max_level={max_level}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.immobiliare.it/',
        'Origin': 'https://www.immobiliare.it',
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Not A;Brand";v="99", "Chromium";v="101"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    
    try:
        logger.info(f"Querying API for zones matching '{query}'")
        response = requests.get(url, headers=headers)
        
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(delay_range[0], delay_range[1]))
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                logger.info(f"Found {len(data)} results for query '{query}'")
                return data
            else:
                logger.warning(f"No results found for query '{query}'")
                return []
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return []
    
    except Exception as e:
        logger.error(f"Error querying API: {e}")
        return []

def process_zone_data(zone_data, common_cities):
    """
    Process zone data from API and update common_cities dictionary
    
    Args:
        zone_data: List of zone data entries from API
        common_cities: Current common_cities dictionary to update
        
    Returns:
        Updated common_cities dictionary
    """
    for zone in zone_data:
        zone_id = zone.get("id")
        zone_type = zone.get("type")
        zone_label = zone.get("label")
        zone_keyurl = zone.get("keyurl")
        
        # Skip if not a zone (type 3)
        if zone_type != 3 or not zone_id or not zone_label:
            continue
            
        # Get parent info (comune/city)
        parents = zone.get("parents", [])
        comune_info = None
        
        for parent in parents:
            # Look for comune (type 2)
            if parent.get("type") == 2:
                comune_info = parent
                break
        
        if not comune_info:
            logger.warning(f"No comune found for zone '{zone_label}', skipping")
            continue
            
        comune_id = comune_info.get("id")
        comune_label = comune_info.get("label", "")
        comune_keyurl = comune_info.get("keyurl", "").lower()
        
        if not comune_id or not comune_label:
            logger.warning(f"Invalid comune data for zone '{zone_label}', skipping")
            continue
            
        # Check if we need to add the city to common_cities
        if comune_keyurl not in common_cities:
            logger.info(f"Adding new city: {comune_label} (ID: {comune_id})")
            common_cities[comune_keyurl] = {
                "idComune": comune_id,
                "name": comune_label,
                "path": f"/{comune_keyurl}/",
                "macrozones": {}
            }
        
        # Clean zone label to create a key (lowercase, replace spaces with underscores)
        zone_key = zone_keyurl.lower().replace('-', '_')
        
        # Add the zone to the city's macrozones if not already present
        if zone_key not in common_cities[comune_keyurl].get("macrozones", {}):
            logger.info(f"Adding zone '{zone_label}' (ID: {zone_id}) to city '{comune_label}'")
            
            # Ensure macrozones key exists
            if "macrozones" not in common_cities[comune_keyurl]:
                common_cities[comune_keyurl]["macrozones"] = {}
            
            common_cities[comune_keyurl]["macrozones"][zone_key] = {
                "id": zone_id,
                "name": zone_label
            }
    
    return common_cities

def populate_zones_for_queries(queries, max_level=3, delay_range=(1.0, 2.0)):
    """
    Populate zone data for a list of queries
    
    Args:
        queries: List of search queries for zones/neighborhoods
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
    
    # Process each query
    for query in queries:
        if not query.strip():
            continue
            
        logger.info(f"Processing query: '{query}'")
        
        # Query API for zone data
        zone_data = query_zone_data(query, max_level, delay_range)
        
        if zone_data:
            # Process and update common cities data
            common_cities = process_zone_data(zone_data, common_cities)
    
    # Save updated data
    if save_common_cities(common_cities):
        logger.info("Successfully updated common_cities.json with zone data")
    else:
        logger.error("Failed to save updated zone data")
    
    return common_cities

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Populate zone data in common_cities.json from Immobiliare.it API')
    parser.add_argument('queries', nargs='+', help='Search queries for zones/neighborhoods (e.g., "Pegli, Multedo" "Castelletto")')
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
    
    # Populate zones
    populate_zones_for_queries(
        queries=args.queries,
        max_level=args.max_level,
        delay_range=(args.min_delay, args.max_delay)
    )

if __name__ == "__main__":
    main()
