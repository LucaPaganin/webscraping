#!/usr/bin/env python3
# --- extract_genova_zones.py ---

import json
import requests
import logging
import time
import random
import sys
from pathlib import Path
from datetime import datetime
from filter_utils import filter_items_by_parent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zone_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
COMMON_CITIES_FILE = Path(__file__).resolve().parent / "common_cities.json"
ZONES_FILE = Path(__file__).resolve().parent / "genova_zones.json"
BACKUP_DIR = Path(__file__).resolve().parent / "backups"
API_URL = "https://www.immobiliare.it/api-next/geography/autocomplete/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.immobiliare.it/',
    'Origin': 'https://www.immobiliare.it',
}

def backup_common_cities():
    """Create a backup of the common_cities.json file."""
    try:
        # Create backup directory if it doesn't exist
        BACKUP_DIR.mkdir(exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"common_cities_backup_{timestamp}.json"
        
        # Read and write the backup
        with open(COMMON_CITIES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Created backup: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False

def load_common_cities():
    """Load the common_cities.json file."""
    try:
        with open(COMMON_CITIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {COMMON_CITIES_FILE}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        return {}

def load_genova_zones():
    """Load the genova_zones.json file."""
    try:
        with open(ZONES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {ZONES_FILE}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        return []

def save_common_cities(data):
    """Save data to the common_cities.json file."""
    try:
        with open(COMMON_CITIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved data to {COMMON_CITIES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save data: {e}")
        return False

def query_zone_info(zone_name):
    """Query the Immobiliare.it API for zone information."""
    query_params = {
        "query": zone_name,
        "max_level": "3"
    }
    
    try:
        response = requests.get(API_URL, params=query_params, headers=HEADERS)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"API returned status code {response.status_code} for '{zone_name}'")
            return []
    except requests.RequestException as e:
        logger.error(f"Request error for '{zone_name}': {e}")
        return []

def extract_zone_data_for_genova():
    """Extract zone data for Genova from the API."""
    # Load the common cities data
    common_cities = load_common_cities()
    if not common_cities:
        logger.error("Failed to load common_cities.json")
        return False
    
    # Load the list of Genova zones
    zones = load_genova_zones()
    if not zones:
        logger.error("Failed to load genova_zones.json")
        return False
    
    # Create a backup before making changes
    if not backup_common_cities():
        logger.warning("Proceeding without backup")
    
    # Initialize zones data for Genova
    if "genova" not in common_cities:
        logger.error("Genova not found in common_cities.json")
        return False
    
    # Initialize the zones object if it doesn't exist
    if "zones" not in common_cities["genova"]:
        common_cities["genova"]["zones"] = {}
    
    # Process each zone
    for zone_name in zones:
        logger.info(f"Processing zone: {zone_name}")
        
        # Query the API for this zone
        results = query_zone_info(zone_name)
        
        if not results:
            logger.warning(f"No results found for zone: {zone_name}")
            continue
        
        # Filter items to find those with Genova as parent
        filtered_items = filter_items_by_parent(results, parent_name="Genova", parent_type=2)
        
        if not filtered_items:
            logger.warning(f"No matching items found for zone: {zone_name}")
            continue
        
        # Use the first matching item
        zone_data = filtered_items[0]
        
        # Extract zone ID and other relevant data
        zone_id = zone_data.get("id")
        if not zone_id:
            logger.warning(f"No ID found for zone: {zone_name}")
            continue
        
        # Convert zone name to a key format (lowercase, replace spaces with underscores)
        zone_key = zone_name.lower().replace(", ", "_").replace(" ", "_").replace(",", "_").replace("'", "")
        
        # Add zone data to common_cities
        common_cities["genova"]["zones"][zone_key] = {
            "id": zone_id,
            "name": zone_name,
            "keyurl": zone_data.get("keyurl", "")
        }
        
        logger.info(f"Added zone: {zone_name} (ID: {zone_id})")
        
        # Add a short delay to avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
    
    # Save updated data
    if save_common_cities(common_cities):
        logger.info("Successfully updated common_cities.json with Genova zones")
        return True
    else:
        logger.error("Failed to save updated data")
        return False

if __name__ == "__main__":
    logger.info("Starting Genova zones extraction")
    
    success = extract_zone_data_for_genova()
    
    if success:
        logger.info("Extraction completed successfully")
    else:
        logger.error("Extraction failed")
        sys.exit(1)
