# --- fetch_ads.py ---

import requests
import time
import random
import uuid
import os
import json
import logging
import argparse
import pandas as pd
from helpers import (
    RealEstateAd, 
    init_cosmos_client, 
    create_ads_dataframe
)
from sqlite_helpers import write_df_to_sqlite, init_database
from dotenv import load_dotenv
from pathlib import Path


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            "PHPSESSID": os.environ.get("PHPSESSID", "261259b2f3205e4d8af334409e133608"),
            "IMMSESSID": os.environ.get("IMMSESSID", "e463dc3c67fb3bbc2073da5b3b8fcfed"),
            "datadome": os.environ.get("DATADOME", "ZnImBoJV2dM48t4Iu5nU7ck38KHj3OHw9PdKsd5MGE8DG1uYGMQuPfajekYwosSQ47MmFDjX4eEd2U0hJeXzPivAOZgqzfdOeuwB7H0P2BA4_SmEookSrO85K9f4HRfV")
        }
    }
    
    return env_vars


# Default headers for API requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.immobiliare.it",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

# Parameters mapper for different cities
def get_params_mapper(contract_type):
    """
    Get the parameters mapper for different cities based on contract type.
    
    Args:
        contract_type: 'rent' or 'sale'
    
    Returns:
        Dictionary mapping city names to API parameters
    """
    if contract_type == "rent":
        path_start = "affitto-case"
        id_contratto = "2"
    else:  # sale
        path_start = "vendita-case"
        id_contratto = "1"
        
    return {
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

# FETCH E UPLOAD

def load_data_from_dict(data_dict):
    """
    Load data from a dictionary and insert it into the Cosmos DB container.

    Args:
        data_dict: The dictionary containing the data to be loaded.
    """
    results = data_dict["results"]
    ads = []

    for item in results:
        try:
            ad = RealEstateAd.model_validate(item["realEstate"])
            ads.append(ad)
        except Exception as e:
            logger.info("[ERRORE] Parsing fallito:", e)
    
    return ads

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
                logger.info("[ERROR] No pages found.")
                break
            logger.info(f"[INFO] page {page} of {max_pages}")
            if page > max_pages:
                logger.info("[INFO] All pages have been processed.")
                break
            
            for item in data["results"]:
                ads.append(item)
                logger.info(f"[OK] fetched ad '{item['realEstate']['title']}'")
        else:
            logger.info(f"[ERRORE] Status code {response.status_code}, interrotto.")
            break

        # Random delay between requests
        min_delay, max_delay = delay_range
        time.sleep(random.uniform(min_delay, max_delay))
        page += 1
    
    df = create_ads_dataframe(ads)
    
    return df

def process_ads(config):
    """
    Main function to process real estate ads.
    
    Args:
        config: Dictionary containing configuration parameters
    """
    contract_type = config.get("contract_type", "rent")
    cosmos_container_name = f"ads_{contract_type}"
    city = config.get("city", "genova")
    max_pages = config.get("max_pages", 1)
    start_page = config.get("start_page", 1)
    base_url = config.get("base_url")
    headers = config.get("headers", DEFAULT_HEADERS)
    cookies = config.get("cookies", {})
    cosmos_endpoint = config.get("cosmos_endpoint", "")
    cosmos_key = config.get("cosmos_key", "")
    cosmos_db = config.get("cosmos_db", "")
    output_path = config.get("output_path", ".")
    save_to_cosmos = config.get("save_to_cosmos", True)
    save_to_sqlite = config.get("save_to_sqlite", False)
    save_to_csv = config.get("save_to_csv", True)
    save_to_json = config.get("save_to_json", False)
    sqlite_db_path = config.get("sqlite_db_path", f"{output_path}/ads.db")
    
    # Get parameters mapper for the selected contract type
    params_mapper = get_params_mapper(contract_type)
    
    # Get the parameters for the selected city
    area_params = params_mapper.get(city, {})
    area_params["pag"] = start_page
    logger.info(f"[INFO] Parametri di ricerca per {city}: {area_params}")
    
    # Fetch the ads
    df = fetch_ads(
        area_params=area_params,
        base_url=base_url,
        headers=headers,
        cookies=cookies,
        max_pages=max_pages,
        start_page=start_page
    )
    logger.info(f"[INFO] Numero di annunci trovati: {len(df)}")
    
    # Clean the DataFrame for export to ensure consistency across formats
    clean_df = clean_dataframe_for_export(df)
    
    # Save to Cosmos DB if requested
    if save_to_cosmos and cosmos_endpoint and cosmos_key and cosmos_db:
        # Initialize Cosmos DB client
        container_client = init_cosmos_client(cosmos_endpoint, cosmos_key, cosmos_db, cosmos_container_name)
        logger.info(f"[INFO] Client Cosmos DB inizializzato per il container: {cosmos_container_name}")
        
        # Convert cleaned DataFrame to records for insertion
        records = clean_df.to_dict('records')
        
        # Add ID and partition key for Cosmos DB
        for record in records:
            if 'uuid' in record and record['uuid']:
                record['id'] = str(record['uuid'])  # Cosmos DB requires a unique ID
            else:
                record['id'] = str(uuid.uuid4())    # Generate UUID if not present
            
            # Ensure partition key (city) is present
            if 'city' not in record or not record['city']:
                record['city'] = city  # Use current city as fallback
        
        # Insert records into Cosmos DB
        successful_inserts = 0
        for i, record in enumerate(records):
            try:
                container_client.upsert_item(body=record)
                successful_inserts += 1
                if i % 10 == 0:  # Log every 10 records to avoid flooding the logs
                    logger.info(f"[INFO] Inserito record {i+1}/{len(records)}")
            except Exception as e:
                logger.error(f"[ERRORE] Inserimento fallito per record {i+1}: {e}")
        
        logger.info(f"[INFO] Inserimento completato. {successful_inserts}/{len(records)} record inseriti in Cosmos DB")
    
    # Save to SQLite if requested
    if save_to_sqlite:
        try:
            # Initialize the database if it doesn't exist
            init_database(sqlite_db_path)
            
            # Write cleaned DataFrame to SQLite
            new_records, updated_records = write_df_to_sqlite(clean_df, sqlite_db_path, replace_existing=True)
            logger.info(f"[INFO] SQLite: {new_records} nuovi record, {updated_records} record aggiornati")
        except Exception as e:
            logger.error(f"[ERRORE] Errore durante il salvataggio in SQLite: {e}")
    
    # Save to CSV if requested
    if save_to_csv:
        try:
            output_filename = f"{output_path}/ads_{city}_{contract_type}.csv"
            clean_df.to_csv(output_filename, index=False)
            logger.info(f"[INFO] Dati salvati nel file CSV: {output_filename}")
        except Exception as e:
            logger.error(f"[ERRORE] Errore durante il salvataggio in CSV: {e}")
    
    # Save to JSON if requested
    if save_to_json:
        try:
            # Convert cleaned DataFrame to list of dictionaries
            records = clean_df.to_dict('records')
            json_filename = f"{output_path}/ads_{city}_{contract_type}.json"
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
                
            logger.info(f"[INFO] Dati salvati nel file JSON: {json_filename}")
        except Exception as e:
            logger.error(f"[ERRORE] Errore durante il salvataggio in JSON: {e}")
    
    return df

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Fetch real estate ads from immobiliare.it')
    parser.add_argument('--city', '-c', type=str, default='genova',
                        help='City to search for ads (default: genova)')
    parser.add_argument('--contract', '-t', type=str, choices=['rent', 'sale'], default='rent',
                        help='Contract type: rent or sale (default: rent)')
    parser.add_argument('--max-pages', '-m', type=lambda x: int(x) if x else None, default=1,
                        help='Maximum number of pages to fetch (default: 1)')
    parser.add_argument('--start-page', '-s', type=int, default=1,
                        help='Page to start fetching from (default: 1)')
    parser.add_argument('--output-path', '-o', type=str, default='.',
                        help='Path where to save the output files (default: current directory)')
    parser.add_argument('--no-save-cosmos', action='store_false', dest='save_cosmos', default=True,
                        help='Do not save data to Cosmos DB')
    parser.add_argument('--save-sqlite', action='store_true', default=False,
                        help='Save data to SQLite database')
    parser.add_argument('--save-csv', action='store_true', default=True,
                        help='Save data to CSV file')
    parser.add_argument('--save-json', action='store_true', default=False,
                        help='Save data to JSON file as a list of dictionaries')
    parser.add_argument('--sqlite-path', type=str, default=None,
                        help='Path to SQLite database file (default: output-path/ads.db)')
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load environment variables
    env_vars = load_env_vars()
    
    max_pages = args.max_pages
    if max_pages is None or max_pages <= 0:
        max_pages = None
    
    # Build configuration from args and env vars
    config = {
        "contract_type": args.contract,
        "city": args.city,
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
        "sqlite_db_path": args.sqlite_path or f"{args.output_path}/ads.db"
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(config["output_path"], exist_ok=True)
    
    # Process ads with the given configuration
    df = process_ads(config)
    
    logger.info("[INFO] Elaborazione completata con successo.")