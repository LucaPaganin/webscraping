#!/usr/bin/env python3
# --- fetch_immobiliare_ads.py ---
# Unified script to fetch ads from immobiliare.it with optional zone-by-zone processing

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

# Setup logging with optional timestamp in filename
def setup_logging(use_file=False):
    """Setup logging configuration"""
    handlers = [logging.StreamHandler()]
    
    if use_file:
        log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"fetch_ads_{log_timestamp}.log"
        handlers.append(logging.FileHandler(log_filename))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Suppress verbose logs
    logging.getLogger("azure.cosmos").setLevel(logging.WARNING)
    logging.getLogger("pydantic").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize logger (will be properly setup in main)
logger = logging.getLogger(__name__)

# Load common cities from JSON file
COMMON_CITIES_FILE = Path(__file__).resolve().parent / "common_cities.json"
try:
    with open(COMMON_CITIES_FILE, 'r', encoding='utf-8') as f:
        COMMON_CITIES = json.load(f)
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

# Parameters mapper for different cities
def get_comune_id_by_name(query):
    """
    Retrieve the idComune for a given search query using Immobiliare.it's autocomplete API.
    
    Args:
        query: The name of the comune/city to search for
        
    Returns:
        Dictionary containing idComune, name, and path if found, None otherwise
    """
    # Use the global COMMON_CITIES dictionary loaded from the JSON file
    
    # First check if query matches a common city directly
    query_lower = query.lower().strip()
    if query_lower in COMMON_CITIES:
        city_info = COMMON_CITIES[query_lower]
        logger.info(f"[INFO] Found comune from local database: {city_info['name']} (ID: {city_info['idComune']})")
        return city_info
    
    # Try multiple API endpoints to increase chance of success
    urls = [
        f"https://www.immobiliare.it/api-next/geography/autocomplete/?query={query}"
    ]
    
    # Common headers to avoid bot detection
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
    
    # Try API endpoints
    for url in urls:
        try:
            logger.info(f"[INFO] Querying comune search API: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # First API format
                if "results" in data:
                    for item in data.get("results", []):
                        if item.get("type") == "comune":
                            comune_info = {
                                "idComune": item.get("id"),
                                "name": item.get("name"),
                                "path": item.get("url", f"/{item.get('name', '').lower().replace(' ', '-')}/")
                            }
                            logger.info(f"[INFO] Found comune from API: {comune_info['name']} (ID: {comune_info['idComune']})")
                            return comune_info
                
                # Second API format
                elif "comune_id" in str(data):
                    for item in data.get("results", []):
                        if item.get("type") == "comune":
                            comune_id = item.get("comune_id")
                            comune_name = item.get("text", "")
                            path = f"/{comune_name.lower().replace(' ', '-')}/"
                            
                            comune_info = {
                                "idComune": str(comune_id),
                                "name": comune_name,
                                "path": path,
                                "provincia_id": item.get("provincia_id"),
                                "regione_id": item.get("regione_id")
                            }
                            logger.info(f"[INFO] Found comune from API: {comune_info['name']} (ID: {comune_info['idComune']})")
                            return comune_info
            
            logger.warning(f"[WARNING] API returned status code {response.status_code} for {url}")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"[WARNING] Error with {url}: {e}")
    
    # Fuzzy match with common cities as a last resort
    best_match = None
    best_score = 0
    for city, info in COMMON_CITIES.items():
        similarity = 0
        query_parts = query_lower.split()
        city_parts = city.split()
        
        # Simple matching algorithm
        for qp in query_parts:
            for cp in city_parts:
                if qp in cp or cp in qp:
                    similarity += 1
        
        if similarity > best_score:
            best_score = similarity
            best_match = info
    
    if best_match and best_score > 0:
        logger.info(f"[INFO] Found closest matching comune: {best_match['name']} (ID: {best_match['idComune']})")
        return best_match
    
    logger.warning(f"[WARNING] No comune found for query: {query}")
    return None

def get_params_mapper(contract_type, comune_id=None, comune_name=None, macrozones=None, region=None):
    """
    Get the parameters mapper for different cities based on contract type.
    
    Args:
        contract_type: 'rent' or 'sale'
        comune_id: Optional idComune parameter
        comune_name: Optional name of the comune for path construction
        macrozones: Optional list of macrozone IDs to filter results
        region: Optional region code (e.g., 'lig' for Liguria)
        
    Returns:
        Dictionary mapping city names to API parameters
    """
    if contract_type == "rent":
        path_start = "affitto-case"
        id_contratto = "2"
    else:  # sale
        path_start = "vendita-case"
        id_contratto = "1"
      # If comune_id is provided, create a custom entry for it
    if comune_id and comune_name:
        formatted_name = comune_name.lower().replace(' ', '-')
        params = {
            "fkRegione": region,  # Use the provided region if available
            "idNazione": "IT",
            "idComune": comune_id,
            "idContratto": id_contratto,
            "idCategoria": "1",
            "__lang": "it",
            "pag": 1,
            "paramsCount": 0,
            "path": f"/{path_start}/{formatted_name}/"
        }
        
        # Add macrozones if provided
        if macrozones and len(macrozones) > 0:
            # Add each macrozone as separate parameters (idMZona[0], idMZona[1], etc.)
            for i, zone_id in enumerate(macrozones):
                params[f"idMZona[{i}]"] = zone_id
                params["paramsCount"] += 1
            
            logger.info(f"[INFO] Added macrozones filter: {macrozones}")
        
        return {
            comune_name.lower(): params
        }
    
    base_params = {
        "genova": {
            "fkRegione": "lig",
            "idProvincia": "GE",
            "idNazione": "IT",
            "idContratto": id_contratto,
            "idCategoria": "1",
            "__lang": "it",
            "pag": 1,
            "paramsCount": 0,
            "path": f"/{path_start}/genova/"
        },
        "savona": {
            "fkRegione": "lig",
            "idProvincia": "SV",
            "idNazione": "IT",
            "idContratto": id_contratto,
            "idCategoria": "1",
            "__lang": "it",
            "pag": 1,
            "paramsCount": 0,
            "path": f"/{path_start}/savona-comune/"
        },
        # Add other cities and their parameters here
    }
    
    # If macrozones are provided, add them to the parameters
    if macrozones and len(macrozones) > 0:
        for city_name, params in base_params.items():
            # Add each macrozone as separate parameters (idMZona[0], idMZona[1], etc.)
            for i, zone_id in enumerate(macrozones):
                params[f"idMZona[{i}]"] = zone_id
                params["paramsCount"] += 1
            
        logger.info(f"[INFO] Added macrozones filter: {macrozones}")
    
    return base_params

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

def save_data(df, city, zone_name=None, zone_id=None, contract_type="rent", config=None):
    """
    Save dataframe data to various formats based on configuration
    
    Args:
        df: DataFrame with ad data
        city: City name
        zone_name: Zone name (optional)
        zone_id: Zone ID (optional)
        contract_type: 'rent' or 'sale'
        config: Dictionary with saving configuration
        
    Returns:
        Dictionary with results information
    """
    # Handle case where config is None
    if config is None:
        config = {}
    
    # Clean the DataFrame for export
    clean_df = clean_dataframe_for_export(df)
    
    # Store operation results for summary
    results = {
        "cosmos_db": {"attempted": False, "success": False, "records": 0, "error": None},
        "sqlite": {"attempted": False, "success": False, "new": 0, "updated": 0, "error": None},
        "csv": {"attempted": False, "success": False, "file": None, "error": None},
        "json": {"attempted": False, "success": False, "file": None, "error": None}
    }
    
    # Add zone info to each record if provided
    if zone_id:
        clean_df['zone_id'] = zone_id
    if zone_name:
        clean_df['zone_name'] = zone_name
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure output directory exists
    output_path = config.get("output_path", ".")
    os.makedirs(output_path, exist_ok=True)
    
    # Create filename based on whether zone info is provided
    if zone_name and zone_id:
        zone_key = zone_name.lower().replace(' ', '_').replace(',', '_').replace("'", "")
        base_filename = f"ads_{city}_{zone_key}_{contract_type}_{timestamp}"
    else:
        base_filename = f"ads_{city}_{contract_type}_{timestamp}"
    
    # Save to Cosmos DB if requested
    if config.get("save_to_cosmos") and config.get("cosmos_endpoint") and config.get("cosmos_key") and config.get("cosmos_db"):
        results["cosmos_db"]["attempted"] = True
        try:
            # Determine container name based on whether zone info is provided
            container_name = f"ads_{contract_type}_zones" if zone_name else f"ads_{contract_type}"
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
            sqlite_db_path = config.get("sqlite_db_path", f"{output_path}/ads.db")
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
    if config.get("save_to_csv", True):  # Default to True
        results["csv"]["attempted"] = True
        try:
            output_filename = f"{output_path}/{base_filename}.csv"
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
            json_filename = f"{output_path}/{base_filename}.json"
            
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

def process_single_query(city, config):
    """
    Process ads for a city with optional macrozones filter
    
    Args:
        city: City name
        config: Configuration dictionary
        
    Returns:
        DataFrame with fetched data
    """
    # Get city info if needed for macrozones
    city_info = None
    if config.get("macrozone_names"):
        city_info = COMMON_CITIES.get(city.lower())
        if not city_info:
            logger.error(f"[ERROR] City '{city}' not found in common_cities.json")
            return pd.DataFrame()
    
    # Resolve macrozone names to IDs if provided
    macrozones = config.get("macrozones", []).copy()
    if config.get("macrozone_names") and city_info and "macrozones" in city_info:
        for name in config.get("macrozone_names", []):
            name_lower = name.lower()
            if name_lower in city_info["macrozones"]:
                macrozone_id = city_info["macrozones"][name_lower]["id"]
                if macrozone_id not in macrozones:
                    macrozones.append(macrozone_id)
                    logger.info(f"[INFO] Found macrozone ID for '{name}': {macrozone_id}")
            else:
                logger.warning(f"[WARNING] Macrozone '{name}' not found for city {city}")
    
    # Update config with resolved macrozones
    config["macrozones"] = macrozones
      # Get parameters mapper for the selected contract type
    params_mapper = get_params_mapper(
        config.get("contract_type", "rent"),
        config.get("comune_id"),
        config.get("comune_name"),
        macrozones,
        config.get("region")
    )
    
    # Get the parameters for the selected city
    area_params = params_mapper.get(city.lower(), {})
    if not area_params:
        logger.error(f"[ERROR] No parameters found for city: {city}")
        return pd.DataFrame()
    
    area_params["pag"] = config.get("start_page", 1)
    logger.info(f"[INFO] Search parameters for {city}: {area_params}")
    
    # Fetch the ads
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
    logger.info(f"[INFO] Found {num_ads} ads for {city}")
    
    # Save the data if ads were found
    if num_ads > 0:
        save_data(df, city, contract_type=config.get("contract_type", "rent"), config=config)
    
    return df

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
    
    # Create combined dataframe if we have data and save_combined_results is True
    if all_ads and config.get("save_combined_results", True):
        combined_df = pd.concat(all_ads, ignore_index=True)
        
        # Save combined data
        logger.info(f"\n[INFO] ===== Saving combined data for all zones =====")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = config.get("output_path", ".")
        
        try:
            # Use save_data function to save combined results
            save_data(
                combined_df, 
                city, 
                zone_name="all_zones", 
                contract_type=config.get("contract_type", "rent"), 
                config=config
            )
            logger.info(f"[INFO] Combined data saved successfully")
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
    
    # Check for macrozones
    if "macrozones" in city_info and city_info["macrozones"]:
        logger.info(f"\n[INFO] Available macrozones for {city_info['name']} (ID: {city_info['idComune']}):")
        for key, macrozone in city_info["macrozones"].items():
            logger.info(f"  - {macrozone['name']} (ID: {macrozone['id']}, Key: {key})")
    else:
        logger.info(f"[INFO] No macrozones defined for city '{city}'")
    
    # Check for zones (neighborhoods)
    if "zones" in city_info and city_info["zones"]:
        logger.info(f"\n[INFO] Available zones (neighborhoods) for {city_info['name']} (ID: {city_info['idComune']}):")
        for key, zone in city_info["zones"].items():
            logger.info(f"  - {zone['name']} (ID: {zone['id']}, Key: {key})")
        return True
    else:
        logger.info(f"[INFO] No zones defined for city '{city}'")
        return "macrozones" in city_info and len(city_info["macrozones"]) > 0
    
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='''
        Unified script to fetch real estate ads from immobiliare.it with two processing modes:
        1. Single query mode: Fetches all ads in one query (default)
        2. Zone-by-zone mode: Fetches ads for each zone separately, one at a time (--use-zones)
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Basic parameters
    basic_group = parser.add_argument_group('Basic parameters')
    basic_group.add_argument('--city', '-c', type=str, default='genova',
                        help='City to search for ads (default: genova)')
    basic_group.add_argument('--contract', '-t', type=str, choices=['rent', 'sale'], default='rent',
                        help='Contract type: rent or sale (default: rent)')
    basic_group.add_argument('--max-pages', '-m', type=lambda x: int(x) if x else None, default=1,
                        help='Maximum number of pages to fetch per query or zone (default: 1, use 0 for all pages)')
    basic_group.add_argument('--start-page', '-s', type=int, default=1,
                        help='Page to start fetching from (default: 1)')
    basic_group.add_argument('--output-path', '-o', type=str, default='.',
                        help='Path where to save the output files (default: current directory)')
    basic_group.add_argument('--log-to-file', action='store_true', default=False,
                        help='Save logs to a timestamped file in addition to console output')
      # City parameters
    city_group = parser.add_argument_group('City parameters (advanced)')
    city_group.add_argument('--comune-query', type=str, default=None,
                        help='Search query to find a comune by name. This will override --city if specified.')
    city_group.add_argument('--comune-id', type=str, default=None,
                        help='Specify idComune directly. Use together with --comune-name. This will override --city and --comune-query if specified.')
    city_group.add_argument('--comune-name', type=str, default=None,
                        help='Name of the comune when specifying comune-id. Required if using --comune-id.')
    city_group.add_argument('--region', type=str, default=None,
                        help='Region code for the city (e.g., "lig" for Liguria). Used to set fkRegione in API parameters.')
    
    # Zone parameters
    zone_group = parser.add_argument_group('Zone parameters')
    zone_group.add_argument('--use-zones', action='store_true',
                       help='Process each zone separately, one at a time. This fetches ads for each zone individually and saves results between zones.')
    zone_group.add_argument('--list-zones', action='store_true',
                       help='List available zones and macrozones for the selected city and exit without fetching any ads')
    zone_group.add_argument('--macrozones', type=str, nargs='+', default=[],
                       help='List of macrozone IDs to filter results. Example: --macrozones 10001 10002')
    zone_group.add_argument('--macrozone-names', type=str, nargs='+', default=[],
                       help='List of macrozone names to filter results. Example: --macrozone-names centro foce')
    zone_group.add_argument('--no-combined-results', action='store_false', dest='save_combined_results', default=True,
                       help='When using --use-zones, do not save combined results from all zones')
    
    # Output format parameters
    output_group = parser.add_argument_group('Output format parameters')
    output_group.add_argument('--save-csv', action='store_true', default=True,
                         help='Save data to CSV files (default: enabled)')
    output_group.add_argument('--no-save-csv', action='store_false', dest='save_csv',
                         help='Do not save data to CSV files')
    output_group.add_argument('--save-json', action='store_true', default=False,
                         help='Save data to JSON files')
    output_group.add_argument('--save-sqlite', action='store_true', default=False,
                         help='Save data to SQLite database')
    output_group.add_argument('--sqlite-path', type=str, default=None,
                         help='Path to SQLite database file (default: output-path/ads.db for single query mode, output-path/ads_zones.db for zone mode)')
    output_group.add_argument('--save-cosmos', action='store_true', default=False,
                         help='Save data to Cosmos DB (requires proper .env configuration)')
    
    # Add examples section
    parser.epilog = '''
Examples:
  # List available zones for Genova
  python fetch_immobiliare_ads.py --city genova --list-zones
  
  # Fetch rental ads for Genova (1 page only)
  python fetch_immobiliare_ads.py --city genova --contract rent
  
  # Fetch all rental ads for Genova
  python fetch_immobiliare_ads.py --city genova --contract rent --max-pages 0
  
  # Fetch all sale ads for Genova, zone by zone
  python fetch_immobiliare_ads.py --city genova --contract sale --max-pages 0 --use-zones
  
  # Fetch ads only for specific macrozones using IDs
  python fetch_immobiliare_ads.py --city genova --macrozones 13297 13298
  
  # Fetch ads only for specific macrozones using names
  python fetch_immobiliare_ads.py --city genova --macrozone-names centro foce
  
  # Save results to multiple formats
  python fetch_immobiliare_ads.py --city genova --save-csv --save-json --save-sqlite --output-path ./data
'''
    
    return parser.parse_args()

def main():
    """Main entry point for the script"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    global logger
    logger = setup_logging(args.log_to_file)
    
    # Load environment variables
    env_vars = load_env_vars()
    
    # If list-zones flag is set, just list the zones and exit
    if args.list_zones:
        list_zones(args.city)
        return
    
    # Process max_pages parameter
    max_pages = args.max_pages
    if max_pages is not None and max_pages <= 0:
        max_pages = None
    
    # Determine city information based on arguments
    comune_id = None
    comune_name = None
    city = args.city
    
    # First check for direct comune ID specification
    if args.comune_id and args.comune_name:
        comune_id = args.comune_id
        comune_name = args.comune_name
        city = args.comune_name.lower()
        logger.info(f"[INFO] Using specified comune: {comune_name} (ID: {comune_id})")
    # Then check for comune query search
    elif args.comune_query:
        logger.info(f"[INFO] Searching for comune: {args.comune_query}")
        comune_info = get_comune_id_by_name(args.comune_query)
        if comune_info:
            comune_id = comune_info["idComune"]
            comune_name = comune_info["name"]
            city = comune_name.lower()
            logger.info(f"[INFO] Found comune: {comune_name} (ID: {comune_id})")
        else:
            logger.warning(f"[WARNING] Comune not found for query: {args.comune_query}. Using default city: {city}")
      # Build configuration from args and env vars
    config = {
        "contract_type": args.contract,
        "city": city,
        "comune_id": comune_id,
        "comune_name": comune_name,
        "region": args.region,
        "macrozones": args.macrozones,
        "macrozone_names": args.macrozone_names,
        "max_pages": max_pages,
        "start_page": args.start_page,
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
        "save_combined_results": args.save_combined_results,
        "sqlite_db_path": args.sqlite_path or (
            f"{args.output_path}/ads_zones.db" if args.use_zones else f"{args.output_path}/ads.db"
        ),
        "use_zones": args.use_zones,
        "delay_range": (2.5, 5.0)  # Default delay between requests
    }
      # Log the run configuration
    logger.info(f"[CONFIG] City: {city}")
    logger.info(f"[CONFIG] Contract type: {config['contract_type']}")
    logger.info(f"[CONFIG] Processing mode: {'zone-by-zone' if args.use_zones else 'single query'}")
    logger.info(f"[CONFIG] Maximum pages: {max_pages if max_pages is not None else 'All'}")
    logger.info(f"[CONFIG] Output path: {config['output_path']}")
    
    if config['region']:
        logger.info(f"[CONFIG] Region: {config['region']}")
    if config['macrozones']:
        logger.info(f"[CONFIG] Using macrozone filters: {config['macrozones']}")
    if config['macrozone_names']:
        logger.info(f"[CONFIG] Using macrozone name filters: {config['macrozone_names']}")
    
    # Create output directory if it doesn't exist
    os.makedirs(config["output_path"], exist_ok=True)
    
    # Start time for total runtime calculation
    start_time = time.time()
    
    # Choose processing mode
    if args.use_zones:
        logger.info(f"[INFO] Using zone-by-zone processing for {city}")
        results = process_all_zones(city, config)
        
        if results["success"]:
            logger.info(f"[INFO] Zone-by-zone processing completed successfully")
            logger.info(f"[INFO] Processed {results['zones_processed']}/{results['total_zones']} zones")
            logger.info(f"[INFO] Found {results['total_ads']} total ads")
        else:
            logger.error(f"[ERROR] Zone-by-zone processing failed")
    else:
        logger.info(f"[INFO] Using single query processing for {city}")
        df = process_single_query(city, config)
        logger.info(f"[INFO] Single query processing completed. Found {len(df)} ads.")
    
    # Calculate and display total runtime
    end_time = time.time()
    total_runtime = end_time - start_time
    hours, remainder = divmod(total_runtime, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    logger.info(f"[INFO] Total runtime: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
    logger.info("[INFO] All operations completed")

if __name__ == "__main__":
    main()
