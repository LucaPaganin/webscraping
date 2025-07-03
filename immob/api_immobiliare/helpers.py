# --- helpers.py ---

from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from uuid import UUID
from azure.cosmos import CosmosClient, exceptions, ContainerProxy
from models import RealEstateAd
import pandas as pd

# INIZIALIZZAZIONE COSMOS

def init_cosmos_client(endpoint: str, key: str, db_name: str, container_name: str):
    client = CosmosClient(endpoint, credential=key)
    db = client.get_database_client(db_name)
    container = db.create_container_if_not_exists(container_name, partition_key="city")
    return container

# INSERIMENTO SINGOLO ANNUNCIO

def insert_ad(container: ContainerProxy, ad: RealEstateAd):
    try:
        item = ad.model_dump()
        # Convert UUID to string for Cosmos DB
        item['id'] = str(ad.uuid)
        container.upsert_item(item)
        print(f"[OK] insterted ad '{ad.title}'")
    except exceptions.CosmosHttpResponseError as e:
        print(f"[ERROR] insertion failed for ad '{ad.title}': {e.message}")

# ESTRAZIONE DATI IN FORMATO PIATTO

def extract_flat_ad_data(ad_data: dict) -> dict:
    """
    Estrae i dati rilevanti da un annuncio immobiliare e li inserisce in un dizionario
    con tutte le chiavi al primo livello.
    
    Args:
        ad_data: Dizionario contenente i dati dell'annuncio (realEstate)
        
    Returns:
        Dizionario con i dati rilevanti dell'annuncio in formato piatto
    """
    real_estate = ad_data.get("realEstate", {})
    if not real_estate:
        return {}
    
    # Estrai i dati di base dell'annuncio
    flat_data = {
        "id": real_estate.get("id"),
        "uuid": real_estate.get("uuid"),
        "visibility": real_estate.get("visibility"),
        "contract": real_estate.get("contract"),
        "isNew": real_estate.get("isNew"),
        "luxury": real_estate.get("luxury"),
        "title": real_estate.get("title"),
        "type": real_estate.get("type"),
        "typology_id": real_estate.get("typology", {}).get("id"),
        "typology_name": real_estate.get("typology", {}).get("name"),
        "isProjectLike": real_estate.get("isProjectLike"),
        "isMosaic": real_estate.get("isMosaic"),
        "propertiesCount": real_estate.get("propertiesCount"),
        "url": ad_data.get("seo", {}).get("url"),
        "geoHash": ad_data.get("idGeoHash")
    }
    
    # Estrai i dati di prezzo
    price = real_estate.get("price", {})
    flat_data.update({
        "price_value": price.get("value"),
        "price_formatted": price.get("formattedValue"),
        "price_min": price.get("minValue"),
        "price_max": price.get("maxValue"),
        "price_range": price.get("priceRange"),
        "price_visible": price.get("visible")
    })
    
    # Estrai i dati dell'agenzia
    agency = real_estate.get("advertiser", {}).get("agency", {})
    flat_data.update({
        "agency_id": agency.get("id"),
        "agency_type": agency.get("type"),
        "agency_name": agency.get("displayName"),
        "agency_label": agency.get("label"),
        "agency_url": agency.get("agencyUrl")
    })
    
    # Estrai le info sulla proprietà principale (se presente)
    properties = real_estate.get("properties", [])
    if properties:
        main_property = properties[0]
        
        # Aggiungi informazioni sulla proprietà principale
        flat_data.update({
            "surface": main_property.get("surface"),
            "rooms": main_property.get("rooms"),
            "bathrooms": main_property.get("bathrooms"),
            "description": main_property.get("description"),
            "elevator": main_property.get("elevator"),
            "typologyGA4Translation": main_property.get("typologyGA4Translation"),
            "ga4Heating": main_property.get("ga4Heating"),
            "ga4features": ", ".join(main_property.get("ga4features", [])) if main_property.get("ga4features") else None,
            "ga4Garage": main_property.get("ga4Garage"),
            "caption": main_property.get("caption"),
            "matchSearch": main_property.get("matchSearch")
        })
        
        # Aggiungi informazioni sulla posizione
        location = main_property.get("location", {})
        if location:
            flat_data.update({
                "address": location.get("address"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "region": location.get("region"),
                "province": location.get("province"),
                "city": location.get("city"),
                "macrozone": location.get("macrozone"),
                "nation": location.get("nation", {}).get("name")
            })
        
        # Aggiungi informazioni sul piano (se presenti)
        floor = main_property.get("floor", {})
        if floor:
            flat_data.update({
                "floor": floor.get("value"),
                "floor_number": floor.get("floorOnlyValue"),
                "floor_ga4value": floor.get("ga4FloorValue")
            })
        
        # Estrai URL della foto principale
        photo = main_property.get("photo", {})
        if photo:
            urls = photo.get("urls", {})
            flat_data.update({
                "photo_id": photo.get("id"),
                "photo_caption": photo.get("caption"),
                "photo_url_small": urls.get("small"),
                "photo_url_medium": urls.get("medium"),
                "photo_url_large": urls.get("large")
            })
        
        # Estrai viste disponibili
        views = main_property.get("views", [])
        if views:
            flat_data["views"] = ", ".join([view.get("name", "") for view in views])
    
    return flat_data

def create_ads_dataframe(ads_list: list) -> pd.DataFrame:
    """
    Crea un DataFrame pandas a partire da una lista di annunci immobiliari.
    
    Args:
        ads_list: Lista di dizionari contenenti gli annunci immobiliari
        
    Returns:
        pandas.DataFrame contenente tutti gli annunci in formato tabellare
    """
    flat_ads = []
    for ad in ads_list:
        flat_ad = extract_flat_ad_data(ad)
        if flat_ad:
            flat_ads.append(flat_ad)
    
    df = pd.DataFrame(flat_ads)
    
    # Riorganizza le colonne in gruppi logici per migliore leggibilità
    column_groups = [
        # Identificazione
        ["id", "uuid", "title", "url", "geoHash"],
        # Tipo e visibilità
        ["type", "typology_id", "typology_name", "contract", "isNew", "luxury", "visibility", "isProjectLike", "isMosaic", "propertiesCount"],
        # Prezzo
        [col for col in df.columns if col.startswith("price_")],
        # Caratteristiche principali
        ["surface", "rooms", "bathrooms", "floor", "floor_number", "floor_ga4value", "elevator"],
        # Posizione
        ["address", "latitude", "longitude", "city", "province", "region", "macrozone", "nation"],
        # Descrizioni e caratteristiche
        ["description", "caption", "ga4features", "ga4Heating", "ga4Garage", "views"],
        # Agenzia
        [col for col in df.columns if col.startswith("agency_")],
        # Foto
        [col for col in df.columns if col.startswith("photo_")]
    ]
    
    # Appiattisci e filtra per colonne esistenti
    sorted_columns = []
    for group in column_groups:
        sorted_columns.extend([col for col in group if col in df.columns])
    
    # Aggiungi eventuali colonne rimanenti
    remaining_columns = [col for col in df.columns if col not in sorted_columns]
    sorted_columns.extend(remaining_columns)
    
    return df[sorted_columns]

def transform_df_dtypes(df):
    def extract_surface_m2(s):
        """Estrae il valore numerico della superficie da una stringa"""
        if not s:
            return None
        try:
            # Prende la prima parte della stringa e converte in intero
            # es. "95 m²" -> 95
            return int(s.split()[0])
        except (ValueError, IndexError):
            return None

    df['surface_m2'] = df.surface.apply(extract_surface_m2)

    def cast_floor_number(f):
        if not isinstance(f, str):
            return f
        if f.isdigit():
            return int(f)
        if "piano terra" in f or "piano rialzato" in f:
            return 0
        return None

    df['floor_number'] = df['floor_number'].apply(cast_floor_number)