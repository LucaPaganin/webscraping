#!/usr/bin/env python3
# --- fetch_zones_ads.py ---
# Script to fetch ads for each zone in a city, one at a time
# Saves data between each zone call

import requests
import time
import random
import uuid
import os
import json
import logging
import argparse
import pandas as pd
from datetime import datetime
from helpers import (
    RealEstateAd, 
    init_cosmos_client, 
    create_ads_dataframe,
    transform_df_dtypes
)
from sqlite_helpers import write_df_to_sqlite, init_database
from dotenv import load_dotenv
from pathlib import Path

# Setup logging with timestamp in filename
log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"zones_fetch_{log_timestamp}.log"

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress verbose logs
logging.getLogger("azure.cosmos").setLevel(logging.WARNING)
logging.getLogger("pydantic").setLevel(logging.WARNING)

# Load common cities from JSON file
COMMON_CITIES_FILE = Path(__file__).resolve().parent / "common_cities.json"
try:
    with open(COMMON_CITIES_FILE, 'r', encoding='utf-8') as f:
        COMMON_CITIES = json.load(f)
    logger.debug(f"Loaded {len(COMMON_CITIES)} cities from {COMMON_CITIES_FILE}")
except Exception as e:
    logger.error(f"Error loading common_cities.json: {e}")
    COMMON_CITIES = {}

# Load environment variables
def load_env_vars():
    """Load environment variables from .env file"""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    
    # Get environment variables with fallbacks
    env_vars = {
        "COSMOS_ENDPOINT": os.environ.get("COSMOS_DB_ACCOUNT_URI", ""),
        "COSMOS_KEY": os.environ.get("COSMOS_DB_ACCOUNT_KEY", ""),
        "COSMOS_DB": os.environ.get("COSMOS_DB_DATABASE_NAME", ""),
        "BASE_URL": os.environ.get("IMMOBILIARE_API_URL", "https://www.immobiliare.it/api-next/search-list/listings/"),
        "COOKIES": {
            "PHPSESSID": os.environ.get("PHPSESSID", "e5686b96fbe172ee7cd72d2fee24712d"),
            "IMMSESSID": os.environ.get("IMMSESSID", "e463dc3c67fb3bbc2073da5b3b8fcfed"),
            "datadome": os.environ.get("DATADOME", "raRTHfOWVs3UHHI0mL8JHd28BnmNGvrwoW0YQoe1OGWN0396cfnXqNZrH0efDY3YacgoqDuIrgM200pQSPu_HDzKNaXsJwGE6B2_cz_TqXauGiR04B_nuZPm7RCwmRt7")
        }
    }
    
    return env_vars

# Default headers for API requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.immobiliare.it",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

def clean_dataframe_for_export(df):
    """
    Clean DataFrame by replacing NaN values with None and empty strings with None.
    This ensures consistency when saving to JSON or uploading to databases.
    
    Args:
        df: Pandas DataFrame to clean
        
    Returns:
        Cleaned DataFrame with NaN and empty strings replaced with None
    """
    # Make a copy to avoid modifying the original DataFrame
    cleaned_df = df.copy()
    
    # Replace NaN with None (which becomes null in JSON)
    cleaned_df = cleaned_df.astype(object).replace({pd.NA: None})
    cleaned_df = cleaned_df.where(pd.notnull(cleaned_df), None)
    
    # Replace empty strings with None
    for col in cleaned_df.columns:
        if cleaned_df[col].dtype == object:  # Only process string columns
            cleaned_df[col] = cleaned_df[col].replace('', None)
    
    return cleaned_df

def get_params_for_zone(contract_type, comune_info, zone_id):
    """
    Get parameters for a specific zone API call
    
    Args:
        contract_type: 'rent' or 'sale'
        comune_info: Dictionary with commune information
        zone_id: Zone ID to filter results
        
    Returns:
        Dictionary of API parameters
    """
    if contract_type == "rent":
        path_start = "affitto-case"
        id_contratto = "2"
    else:  # sale
        path_start = "vendita-case"
        id_contratto = "1"
    
    comune_name = comune_info.get("name", "").lower().replace(' ', '-')
    comune_id = comune_info.get("idComune")
    
    params = {
        "fkRegione": None,  # Will be determined by the API
        "idNazione": "IT",
        "idComune": comune_id,
        "idContratto": id_contratto,
        "idCategoria": "1",
        "__lang": "it",
        "pag": 1,
        "paramsCount": 1,  # Start at 1 because we have one zone filter
        "path": f"/{path_start}/{comune_name}/",
        "idMZona[0]": zone_id  # Add the zone ID
    }
    
    return params

def fetch_ads(area_params, base_url, headers=None, cookies=None, max_pages=None, start_page=1, delay_range=(2.5, 5.0)):
    """
    Fetch real estate ads from immobiliare.it based on the provided parameters.
    
    Args:
        area_params: Dictionary of parameters for the API
        base_url: Base URL for the API
        headers: Dictionary of HTTP headers (optional)
        cookies: Dictionary of cookies (optional)
        max_pages: Maximum number of pages to fetch (optional)
        start_page: Page to start fetching from (optional, default 1)
        delay_range: Tuple of min/max delay between requests (optional)
        
    Returns:
        DataFrame containing the fetched ads
    """
    session = requests.Session()
    if headers:
        session.headers.update(headers)
    if cookies:
        session.cookies.update(cookies)
    ads = []

    page = start_page
    while not max_pages or page <= max_pages:
        logger.info(f"[INFO] page {page}")
        area_params["pag"] = page

        response = session.get(base_url, params=area_params)
        if response.status_code == 200:
            data = response.json()
            if max_pages is None:
                max_pages = data.get("maxPages", 0)
            if max_pages == 0:
                logger.info("[INFO] No pages found.")
                break
            logger.info(f"[INFO] page {page} of {max_pages}")
            if page > max_pages:
                logger.info("[INFO] All pages have been processed.")
                break
            
            for item in data["results"]:
                ads.append(item)
                logger.info(f"[OK] fetched ad '{item['realEstate']['title']}'")
        else:
            logger.info(f"[ERROR] status code {response.status_code}, response: {response.text}")
            break

        # Random delay between requests
        min_delay, max_delay = delay_range
        time.sleep(random.uniform(min_delay, max_delay))
        page += 1
    
    df = create_ads_dataframe(ads)
    
    return df

def save_data(df, city, zone_name, zone_id, contract_type, config):
    """
    Save dataframe data to various formats based on configuration
    
    Args:
        df: DataFrame with ad data
        city: City name
        zone_name: Zone name
        zone_id: Zone ID
        contract_type: 'rent' or 'sale'
        config: Dictionary with saving configuration
        
    Returns:
        Dictionary with results information
    """
    # Clean the DataFrame for export
    clean_df = clean_dataframe_for_export(df)
    
    # Store operation results for summary
    results = {
        "cosmos_db": {"attempted": False, "success": False, "records": 0, "error": None},
        "sqlite": {"attempted": False, "success": False, "new": 0, "updated": 0, "error": None},
        "csv": {"attempted": False, "success": False, "file": None, "error": None},
        "json": {"attempted": False, "success": False, "file": None, "error": None}
    }
    
    # Add zone info to each record
    clean_df['zone_id'] = zone_id
    clean_df['zone_name'] = zone_name
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure output directory exists
    output_path = config.get("output_path", ".")
    os.makedirs(output_path, exist_ok=True)
    
    # Save to Cosmos DB if requested
    if config.get("save_to_cosmos") and config.get("cosmos_endpoint") and config.get("cosmos_key") and config.get("cosmos_db"):
        results["cosmos_db"]["attempted"] = True
        try:
            # Initialize Cosmos DB client
            container_name = f"ads_{contract_type}_zones"
            container_client = init_cosmos_client(
                config["cosmos_endpoint"], 
                config["cosmos_key"], 
                config["cosmos_db"], 
                container_name
            )
            logger.info(f"[INFO] Cosmos DB client initialized for container: {container_name}")
            
            # Convert cleaned DataFrame to records for insertion
            records = clean_df.to_dict('records')
            
            # Add ID and partition key for Cosmos DB
            for record in records:
                if 'uuid' in record and record['uuid']:
                    record['id'] = str(record['uuid'])
                else:
                    record['id'] = str(uuid.uuid4())
                
                # Ensure partition key (city) is present
                if 'city' not in record or not record['city']:
                    record['city'] = city
            
            # Insert records into Cosmos DB
            successful_inserts = 0
            for i, record in enumerate(records):
                try:
                    container_client.upsert_item(body=record)
                    successful_inserts += 1
                    if i % 10 == 0 or i == len(records) - 1:
                        logger.info(f"[INFO] Inserted record {i+1}/{len(records)}")
                except Exception as record_e:
                    logger.error(f"[ERROR] Failed to insert record {i+1}: {record_e}")
            
            logger.info(f"[INFO] Insertion complete. {successful_inserts}/{len(records)} records inserted in Cosmos DB")
            results["cosmos_db"]["success"] = True
            results["cosmos_db"]["records"] = successful_inserts
        except Exception as e:
            logger.error(f"[ERROR] Failed to save to Cosmos DB: {e}")
            results["cosmos_db"]["error"] = str(e)
    
    # Save to SQLite if requested
    if config.get("save_to_sqlite"):
        results["sqlite"]["attempted"] = True
        try:
            # Initialize the database if it doesn't exist
            sqlite_db_path = config.get("sqlite_db_path", f"{output_path}/ads_zones.db")
            init_database(sqlite_db_path)
            
            # Write cleaned DataFrame to SQLite
            new_records, updated_records = write_df_to_sqlite(clean_df, sqlite_db_path, replace_existing=True)
            logger.info(f"[INFO] SQLite: {new_records} new records, {updated_records} updated records")
            results["sqlite"]["success"] = True
            results["sqlite"]["new"] = new_records
            results["sqlite"]["updated"] = updated_records
        except Exception as e:
            logger.error(f"[ERROR] Failed to save to SQLite: {e}")
            results["sqlite"]["error"] = str(e)
    
    # Save to CSV if requested
    if config.get("save_to_csv"):
        results["csv"]["attempted"] = True
        try:
            zone_key = zone_name.lower().replace(' ', '_').replace(',', '_').replace("'", "")
            output_filename = f"{output_path}/ads_{city}_{zone_key}_{contract_type}_{timestamp}.csv"
            clean_df.to_csv(output_filename, index=False)
            logger.info(f"[INFO] Data saved to CSV file: {output_filename}")
            results["csv"]["success"] = True
            results["csv"]["file"] = output_filename
        except Exception as e:
            logger.error(f"[ERROR] Failed to save to CSV: {e}")
            results["csv"]["error"] = str(e)
    
    # Save to JSON if requested
    if config.get("save_to_json"):
        results["json"]["attempted"] = True
        try:
            # Convert cleaned DataFrame to list of dictionaries
            records = clean_df.to_dict('records')
            zone_key = zone_name.lower().replace(' ', '_').replace(',', '_').replace("'", "")
            json_filename = f"{output_path}/ads_{city}_{zone_key}_{contract_type}_{timestamp}.json"
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
                
            logger.info(f"[INFO] Data saved to JSON file: {json_filename}")
            results["json"]["success"] = True
            results["json"]["file"] = json_filename
        except Exception as e:
            logger.error(f"[ERROR] Failed to save to JSON: {e}")
            results["json"]["error"] = str(e)
    
    # Log summary
    logger.info("[OPERATION SUMMARY]")
    if results["cosmos_db"]["attempted"]:
        status = "✓ Success" if results["cosmos_db"]["success"] else f"✗ Failed ({results['cosmos_db']['error']})"
        logger.info(f"- Cosmos DB: {status}")
    if results["sqlite"]["attempted"]:
        status = "✓ Success" if results["sqlite"]["success"] else f"✗ Failed ({results['sqlite']['error']})"
        logger.info(f"- SQLite: {status}")
    if results["csv"]["attempted"]:
        status = "✓ Success" if results["csv"]["success"] else f"✗ Failed ({results['csv']['error']})"
        logger.info(f"- CSV: {status}")
    if results["json"]["attempted"]:
        status = "✓ Success" if results["json"]["success"] else f"✗ Failed ({results['json']['error']})"
        logger.info(f"- JSON: {status}")
    
    return results

def process_zone_ads(city, zone_name, zone_id, config):
    """
    Process ads for a specific zone
    
    Args:
        city: City name
        zone_name: Zone name
        zone_id: Zone ID
        config: Configuration dictionary
        
    Returns:
        DataFrame with fetched data
    """
    logger.info(f"[INFO] Processing zone: {zone_name} (ID: {zone_id})")
    
    # Get city info
    city_info = COMMON_CITIES.get(city.lower())
    if not city_info:
        logger.error(f"[ERROR] City '{city}' not found in common_cities.json")
        return pd.DataFrame()
    
    # Get parameters for this zone
    area_params = get_params_for_zone(
        config.get("contract_type", "rent"),
        city_info,
        zone_id
    )
    
    logger.info(f"[INFO] API parameters: {area_params}")
    
    # Fetch ads for this zone
    df = fetch_ads(
        area_params=area_params,
        base_url=config.get("base_url"),
        headers=config.get("headers", DEFAULT_HEADERS),
        cookies=config.get("cookies", {}),
        max_pages=config.get("max_pages"),
        start_page=config.get("start_page", 1),
        delay_range=config.get("delay_range", (2.5, 5.0))
    )
    
    num_ads = len(df)
    logger.info(f"[INFO] Found {num_ads} ads for zone '{zone_name}'")
    
    # If we found ads, save the data
    if num_ads > 0:
        save_data(df, city, zone_name, zone_id, config.get("contract_type", "rent"), config)
    
    return df

def process_all_zones(city, config):
    """
    Process ads for all zones in a city
    
    Args:
        city: City name
        config: Configuration dictionary
        
    Returns:
        Dictionary with results summary
    """
    # Get city info
    city_info = COMMON_CITIES.get(city.lower())
    if not city_info:
        logger.error(f"[ERROR] City '{city}' not found in common_cities.json")
        return {"success": False, "error": f"City '{city}' not found"}
    
    # Check if zones are defined for this city
    zones = city_info.get("zones", {})
    if not zones:
        logger.error(f"[ERROR] No zones defined for city '{city}'")
        return {"success": False, "error": f"No zones defined for city '{city}'"}
    
    # Log the number of zones to process
    logger.info(f"[INFO] Processing {len(zones)} zones for {city}")
    
    # Process each zone
    all_ads = []
    zone_results = {}
    
    for zone_key, zone_info in zones.items():
        zone_name = zone_info.get("name")
        zone_id = zone_info.get("id")
        
        if not zone_id:
            logger.warning(f"[WARNING] No ID found for zone '{zone_name}', skipping")
            continue
        
        logger.info(f"\n[INFO] ===== Processing zone: {zone_name} (ID: {zone_id}) =====")
        
        try:
            # Process ads for this zone
            df = process_zone_ads(city, zone_name, zone_id, config)
            
            # Add to results
            num_ads = len(df)
            zone_results[zone_key] = {
                "name": zone_name,
                "id": zone_id,
                "ads_count": num_ads,
                "success": True
            }
            
            # Add to all ads
            if num_ads > 0:
                all_ads.append(df)
                
            # Add delay between zones to avoid rate limiting
            delay = random.uniform(3.0, 6.0)
            logger.info(f"[INFO] Waiting {delay:.2f} seconds before next zone...")
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to process zone '{zone_name}': {e}")
            zone_results[zone_key] = {
                "name": zone_name,
                "id": zone_id,
                "ads_count": 0,
                "success": False,
                "error": str(e)
            }
    
    # Create combined dataframe if we have data
    combined_df = pd.DataFrame()
    if all_ads:
        combined_df = pd.concat(all_ads, ignore_index=True)
        
        # Save combined data
        logger.info(f"\n[INFO] ===== Saving combined data for all zones =====")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = config.get("output_path", ".")
        combined_filename = f"{output_path}/ads_{city}_all_zones_{config.get('contract_type', 'rent')}_{timestamp}.csv"
        
        try:
            combined_df.to_csv(combined_filename, index=False)
            logger.info(f"[INFO] Combined data saved to: {combined_filename}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to save combined data: {e}")
    
    # Log summary
    success_count = sum(1 for result in zone_results.values() if result["success"])
    total_ads = sum(result["ads_count"] for result in zone_results.values())
    
    logger.info(f"\n[INFO] ===== PROCESSING SUMMARY =====")
    logger.info(f"Total zones processed: {success_count}/{len(zones)}")
    logger.info(f"Total ads found: {total_ads}")
    
    return {
        "success": success_count > 0,
        "zones_processed": success_count,
        "total_zones": len(zones),
        "total_ads": total_ads,
        "zone_results": zone_results
    }

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Fetch real estate ads for each zone in a city')
    
    # City parameter
    parser.add_argument('--city', '-c', type=str, default='genova',
                        help='City to search for ads (default: genova)')
    
    # Contract and pagination parameters
    parser.add_argument('--contract', '-t', type=str, choices=['rent', 'sale'], default='rent',
                        help='Contract type: rent or sale (default: rent)')
    parser.add_argument('--max-pages', '-m', type=lambda x: int(x) if x else None, default=1,
                        help='Maximum number of pages to fetch for each zone (default: 1)')
    parser.add_argument('--list-zones', action='store_true',
                        help='List available zones for the selected city and exit')
    
    # Output parameters
    output_group = parser.add_argument_group('Output parameters')
    output_group.add_argument('--output-path', '-o', type=str, default='.',
                        help='Path where to save the output files (default: current directory)')
    output_group.add_argument('--no-save-cosmos', action='store_false', dest='save_cosmos', default=False,
                        help='Do not save data to Cosmos DB (default: do not save)')
    output_group.add_argument('--save-cosmos', action='store_true', dest='save_cosmos',
                        help='Save data to Cosmos DB')
    output_group.add_argument('--no-save-sqlite', action='store_false', dest='save_sqlite', default=False,
                        help='Do not save data to SQLite database (default: do not save)')
    output_group.add_argument('--save-sqlite', action='store_true', dest='save_sqlite',
                        help='Save data to SQLite database')
    output_group.add_argument('--no-save-csv', action='store_false', dest='save_csv', default=True,
                        help='Do not save data to CSV files')
    output_group.add_argument('--save-csv', action='store_true', dest='save_csv',
                        help='Save data to CSV files (default: enabled)')
    output_group.add_argument('--save-json', action='store_true', default=False,
                        help='Save data to JSON files')
    output_group.add_argument('--sqlite-path', type=str, default=None,
                        help='Path to SQLite database file (default: output-path/ads_zones.db)')
    
    return parser.parse_args()

def list_zones(city):
    """
    List available zones for a given city.
    
    Args:
        city: Name of the city to list zones for
        
    Returns:
        True if zones were found and listed, False otherwise
    """
    if not city:
        logger.error("[ERROR] No city provided to list zones")
        return False
    
    city_lower = city.lower()
    
    if city_lower not in COMMON_CITIES:
        logger.error(f"[ERROR] City '{city}' not found in common cities database")
        return False
    
    city_info = COMMON_CITIES[city_lower]
    if "zones" not in city_info or not city_info["zones"]:
        logger.error(f"[ERROR] No zones defined for city '{city}'")
        return False
    
    logger.info(f"\n[INFO] Available zones for {city_info['name']} (ID: {city_info['idComune']}):")
    for key, zone in city_info["zones"].items():
        logger.info(f"  - {zone['name']} (ID: {zone['id']}, Key: {key})")
    
    return True

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Load environment variables
    env_vars = load_env_vars()
    
    # If list-zones flag is set, just list the zones and exit
    if args.list_zones:
        list_zones(args.city)
        return
    
    max_pages = args.max_pages
    if max_pages is not None and max_pages <= 0:
        max_pages = None
    
    # Build configuration
    config = {
        "contract_type": args.contract,
        "max_pages": max_pages,
        "start_page": 1,
        "output_path": args.output_path,
        "base_url": env_vars["BASE_URL"],
        "headers": DEFAULT_HEADERS,
        "cookies": env_vars["COOKIES"],
        "cosmos_endpoint": env_vars["COSMOS_ENDPOINT"],
        "cosmos_key": env_vars["COSMOS_KEY"],
        "cosmos_db": env_vars["COSMOS_DB"],
        "save_to_cosmos": args.save_cosmos,
        "save_to_sqlite": args.save_sqlite,
        "save_to_csv": args.save_csv,
        "save_to_json": args.save_json,
        "sqlite_db_path": args.sqlite_path or f"{args.output_path}/ads_zones.db"
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(config["output_path"], exist_ok=True)
    
    # Process all zones
    logger.info(f"[INFO] Starting processing for all zones in {args.city}")
    results = process_all_zones(args.city, config)
    
    if results["success"]:
        logger.info(f"[INFO] Processing completed successfully")
        logger.info(f"[INFO] Processed {results['zones_processed']}/{results['total_zones']} zones")
        logger.info(f"[INFO] Found {results['total_ads']} total ads")
    else:
        logger.error(f"[ERROR] Processing failed")
    
    logger.info("[INFO] All operations completed")

if __name__ == "__main__":
    main()
