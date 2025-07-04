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

logging.getLogger("azure.cosmos").setLevel(logging.WARNING)  # Suppress Cosmos SDK logs
logging.getLogger("pydantic").setLevel(logging.WARNING)  # Suppress Pydantic validation logs

# Load common cities from JSON file
COMMON_CITIES_FILE = Path(__file__).resolve().parent / "common_cities.json"
try:
    with open(COMMON_CITIES_FILE, 'r', encoding='utf-8') as f:
        COMMON_CITIES = json.load(f)
    logger.debug(f"Loaded {len(COMMON_CITIES)} cities from {COMMON_CITIES_FILE}")
except Exception as e:
    logger.error(f"Error loading common_cities.json: {e}")
    # Fallback to an empty dictionary if the file cannot be loaded
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

def get_params_mapper(contract_type, comune_id=None, comune_name=None):
    """
    Get the parameters mapper for different cities based on contract type.
    
    Args:
        contract_type: 'rent' or 'sale'
        comune_id: Optional idComune parameter
        comune_name: Optional name of the comune for path construction
        
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
        return {
            comune_name.lower(): {
                "fkRegione": None,  # Will be determined by the API
                "idNazione": "IT",
                "idComune": comune_id,
                "idContratto": id_contratto,
                "idCategoria": "1",
                "__lang": "it",
                "pag": 1,
                "paramsCount": 0,
                "path": f"/{path_start}/{formatted_name}/"
            }
        }
        
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
            logger.info(f"[ERROR] status code {response.status_code}, response: {response.text}")
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
    comune_id = config.get("comune_id")
    comune_name = config.get("comune_name")
    max_pages = config.get("max_pages", 1)
    start_page = config.get("start_page", 1)
    base_url = config.get("base_url")
    headers = config.get("headers", DEFAULT_HEADERS)
    cookies = config.get("cookies", {})
    cosmos_endpoint = config.get("cosmos_endpoint", "")
    cosmos_key = config.get("cosmos_key", "")
    cosmos_db = config.get("cosmos_db", "")
    output_path = config.get(
        "output_path", 
        str(
            Path(os.getenv("WINDOWS_HOME", Path.home())) / "onedrive_unige/data/immobiliare.it"
        )
    )
    save_to_cosmos = config.get("save_to_cosmos", True)
    save_to_sqlite = config.get("save_to_sqlite", False)
    save_to_csv = config.get("save_to_csv", True)
    save_to_json = config.get("save_to_json", False)
    sqlite_db_path = config.get("sqlite_db_path", f"{output_path}/ads.db")
    
    # Get parameters mapper for the selected contract type, with comune details if provided
    params_mapper = get_params_mapper(contract_type, comune_id, comune_name)
    
    # Get the parameters for the selected city
    area_params = params_mapper.get(city.lower(), {})
    if not area_params:
        logger.error(f"[ERROR] No parameters found for city: {city}")
        return pd.DataFrame()  # Return empty DataFrame if no parameters found
        
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
    try:
        clean_df = clean_dataframe_for_export(df)
        logger.info(f"[INFO] DataFrame preparato per l'esportazione ({len(clean_df)} record)")
    except Exception as e:
        logger.error(f"[ERRORE] Preparazione del DataFrame fallita: {e}")
        # Create an empty DataFrame as fallback if cleaning fails
        clean_df = pd.DataFrame()
    
    # Store operation results for summary
    results = {
        "cosmos_db": {"attempted": False, "success": False, "records": 0, "error": None},
        "sqlite": {"attempted": False, "success": False, "new": 0, "updated": 0, "error": None},
        "csv": {"attempted": False, "success": False, "file": None, "error": None},
        "json": {"attempted": False, "success": False, "file": None, "error": None}
    }
    
    # Save to Cosmos DB if requested - independent try/except
    if save_to_cosmos and cosmos_endpoint and cosmos_key and cosmos_db:
        results["cosmos_db"]["attempted"] = True
        try:
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
                    if i % 10 == 0 or i == len(records) - 1:  # Log every 10 records and the last one
                        logger.info(f"[INFO] Inserito record {i+1}/{len(records)}")
                except Exception as record_e:
                    logger.error(f"[ERRORE] Inserimento fallito per record {i+1}: {record_e}")
            
            logger.info(f"[INFO] Inserimento completato. {successful_inserts}/{len(records)} record inseriti in Cosmos DB")
            results["cosmos_db"]["success"] = True
            results["cosmos_db"]["records"] = successful_inserts
        except Exception as e:
            logger.error(f"[ERRORE] Salvataggio in Cosmos DB fallito: {e}")
            results["cosmos_db"]["error"] = str(e)
    
    # Save to SQLite if requested - independent try/except
    if save_to_sqlite:
        results["sqlite"]["attempted"] = True
        try:
            # Initialize the database if it doesn't exist
            init_database(sqlite_db_path)
            
            # Write cleaned DataFrame to SQLite
            new_records, updated_records = write_df_to_sqlite(clean_df, sqlite_db_path, replace_existing=True)
            logger.info(f"[INFO] SQLite: {new_records} nuovi record, {updated_records} record aggiornati")
            results["sqlite"]["success"] = True
            results["sqlite"]["new"] = new_records
            results["sqlite"]["updated"] = updated_records
        except Exception as e:
            logger.error(f"[ERRORE] Salvataggio in SQLite fallito: {e}")
            results["sqlite"]["error"] = str(e)
    
    # Save to CSV if requested - independent try/except
    if save_to_csv:
        results["csv"]["attempted"] = True
        try:
            output_filename = f"{output_path}/ads_{city}_{contract_type}.csv"
            clean_df.to_csv(output_filename, index=False)
            logger.info(f"[INFO] Dati salvati nel file CSV: {output_filename}")
            results["csv"]["success"] = True
            results["csv"]["file"] = output_filename
        except Exception as e:
            logger.error(f"[ERRORE] Salvataggio in CSV fallito: {e}")
            results["csv"]["error"] = str(e)
    
    # Save to JSON if requested - independent try/except
    if save_to_json:
        results["json"]["attempted"] = True
        try:
            # Convert cleaned DataFrame to list of dictionaries
            records = clean_df.to_dict('records')
            json_filename = f"{output_path}/ads_{city}_{contract_type}.json"
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
                
            logger.info(f"[INFO] Dati salvati nel file JSON: {json_filename}")
            results["json"]["success"] = True
            results["json"]["file"] = json_filename
        except Exception as e:
            logger.error(f"[ERRORE] Salvataggio in JSON fallito: {e}")
            results["json"]["error"] = str(e)
    
    # Log summary of all operations
    logger.info("[RIEPILOGO OPERAZIONI]")
    if results["cosmos_db"]["attempted"]:
        status = "✓ Successo" if results["cosmos_db"]["success"] else f"✗ Fallito ({results['cosmos_db']['error']})"
        logger.info(f"- Cosmos DB: {status}")
    if results["sqlite"]["attempted"]:
        status = "✓ Successo" if results["sqlite"]["success"] else f"✗ Fallito ({results['sqlite']['error']})"
        logger.info(f"- SQLite: {status}")
    if results["csv"]["attempted"]:
        status = "✓ Successo" if results["csv"]["success"] else f"✗ Fallito ({results['csv']['error']})"
        logger.info(f"- CSV: {status}")
    if results["json"]["attempted"]:
        status = "✓ Successo" if results["json"]["success"] else f"✗ Fallito ({results['json']['error']})"
        logger.info(f"- JSON: {status}")
    
    return df

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Fetch real estate ads from immobiliare.it')
    
    # Location parameters
    location_group = parser.add_argument_group('Location parameters')
    location_group.add_argument('--city', '-c', type=str, default='genova',
                        help='City to search for ads (default: genova)')
    location_group.add_argument('--comune-query', type=str, default=None,
                        help='Search query to find a comune by name. This will override --city if specified.')
    location_group.add_argument('--comune-id', type=str, default=None,
                        help='Specify idComune directly. Use together with --comune-name. This will override --city and --comune-query if specified.')
    location_group.add_argument('--comune-name', type=str, default=None,
                        help='Name of the comune when specifying comune-id. Required if using --comune-id.')
    
    # Contract and pagination parameters
    parser.add_argument('--contract', '-t', type=str, choices=['rent', 'sale'], default='rent',
                        help='Contract type: rent or sale (default: rent)')
    parser.add_argument('--max-pages', '-m', type=lambda x: int(x) if x else None, default=1,
                        help='Maximum number of pages to fetch (default: 1)')
    parser.add_argument('--start-page', '-s', type=int, default=1,
                        help='Page to start fetching from (default: 1)')
    
    # Output parameters
    output_group = parser.add_argument_group('Output parameters')
    output_group.add_argument('--output-path', '-o', type=str, default='.',
                        help='Path where to save the output files (default: current directory)')
    output_group.add_argument('--no-save-cosmos', action='store_false', dest='save_cosmos', default=True,
                        help='Do not save data to Cosmos DB')
    output_group.add_argument('--no-save-sqlite', action='store_false', dest='save_sqlite', default=True,
                        help='Do not save data to SQLite database')
    output_group.add_argument('--save-csv', action='store_true', default=True,
                        help='Save data to CSV file')
    output_group.add_argument('--save-json', action='store_true', default=False,
                        help='Save data to JSON file as a list of dictionaries')
    output_group.add_argument('--sqlite-path', type=str, default=None,
                        help='Path to SQLite database file (default: output-path/ads.db)')
    
    return parser.parse_args()

def main(args: argparse.Namespace):
    # Main logic for fetching ads goes here
    # Load environment variables
    env_vars = load_env_vars()
    
    max_pages = args.max_pages
    if max_pages is None or max_pages <= 0:
        max_pages = None
    
    # Determine comune information based on arguments
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
    
    return df

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    main(args)