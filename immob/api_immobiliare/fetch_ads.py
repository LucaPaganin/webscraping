# --- main.py ---

import requests
import time
import random
import uuid
import os
import json
import sys
import logging
from helpers import (
    RealEstateAd, 
    init_cosmos_client, 
    insert_ad, 
    extract_flat_ad_data, 
    create_ads_dataframe
)
from sqlite_helpers import write_df_to_sqlite, init_database
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PARAMETRI COSMOS DB
COSMOS_ENDPOINT = os.environ["COSMOS_DB_ACCOUNT_URI"]
COSMOS_KEY = os.environ["COSMOS_DB_ACCOUNT_KEY"]
COSMOS_DB = os.environ["COSMOS_DB_DATABASE_NAME"]
COSMOS_CONTAINER = os.environ["COSMOS_DB_CONTAINER_NAME"]

# PARAMETRI DI RICERCA
BASE_URL = "https://www.immobiliare.it/api-next/search-list/listings/"


COOKIES = {
    "PHPSESSID": "261259b2f3205e4d8af334409e133608",
    "IMMSESSID": "e463dc3c67fb3bbc2073da5b3b8fcfed",
    "datadome": "ZnImBoJV2dM48t4Iu5nU7ck38KHj3OHw9PdKsd5MGE8DG1uYGMQuPfajekYwosSQ47MmFDjX4eEd2U0hJeXzPivAOZgqzfdOeuwB7H0P2BA4_SmEookSrO85K9f4HRfV"
}


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.immobiliare.it",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
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

def fetch_ads(area_params, max_pages=None, start_page=1):
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)
    ads = []

    page = start_page
    while not max_pages or page <= max_pages:
        logger.info(f"[INFO] Pagina {page}")
        area_params["pag"] = page

        response = session.get(BASE_URL, params=area_params)
        if response.status_code == 200:
            data = response.json()
            if max_pages is None:
                max_pages = data.get("maxPages", 0)
            if max_pages == 0:
                logger.info("[ERRORE] Nessuna pagina trovata.")
                break
            logger.info(f"[INFO] Pagina {page} di {max_pages}")
            if page > max_pages:
                logger.info("[INFO] Tutte le pagine sono state elaborate.")
                break
            
            for item in data["results"]:
                ads.append(item)
                logger.info(f"[OK] Inserito annuncio {item['realEstate']['title']}")
        else:
            logger.info(f"[ERRORE] Status code {response.status_code}, interrotto.")
            break

        time.sleep(random.uniform(2.5, 5.0))
        page += 1
    
    df = create_ads_dataframe(ads)
    
    return df

if __name__ == "__main__":
    params_mapper = {
        "genova": {
            "fkRegione": "lig",
            "idProvincia": "GE",
            "idNazione": "IT",
            "idContratto": "1",
            "idCategoria": "1",
            "__lang": "it",
            "pag": 1,
            "paramsCount": 0,
            "path": "/{contract}-case/genova-provincia/"
        },
        "savona": {
            "fkRegione": "lig",
            "idProvincia": "SV",
            "idNazione": "IT",
            "idContratto": "1",
            "idCategoria": "1",
            "__lang": "it",
            "pag": 1,
            "paramsCount": 0,
            "path": "/{contract}-case/savona-provincia/"
        },
        # Add other cities and their parameters here
    }
    max_pages = None
    start_page = 1
    city = "savona"
    
    area_params = params_mapper.get(city, {})
    area_params["path"] = area_params["path"].format(contract="vendita")
    area_params["pag"] = start_page
    logger.info(f"[INFO] Parametri di ricerca per {city}: {area_params}")
    
    db_path = "G:/My Drive/HobbyProjects/immob_scraping/ads_db.sqlite"

    df = fetch_ads(area_params, max_pages=max_pages, start_page=start_page)
    logger.info(f"[INFO] Numero di annunci trovati: {len(df)}")
    init_database(db_path)
    write_df_to_sqlite(df, db_path)
    df.to_csv("ads.csv", index=False)
    logger.info(f"[INFO] Dati inseriti nel database SQLite: {db_path}")