"""
SQLite helper functions for storing and retrieving real estate ads.

This module provides functions to:
1. Initialize a SQLite database with the required schema
2. Write a DataFrame of real estate ads to the database
3. Read data from the database with various filtering options
4. Update existing records
5. Delete records
"""

import sqlite3
import pandas as pd
import os
import json
from typing import Optional, List, Dict, Any, Tuple, Union
from contextlib import contextmanager
import logging
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@contextmanager
def get_connection(db_path: str):
    """
    Context manager to handle SQLite database connections.
    
    Args:
        db_path: Path to the SQLite database file
        
    Yields:
        SQLite connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like rows
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def init_database(db_path: str) -> bool:
    """
    Initialize the SQLite database with the required schema.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        True if initialization was successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
              # Create the real_estate_ads table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS real_estate_ads (
                db_id INTEGER PRIMARY KEY AUTOINCREMENT,
                id INTEGER,
                uuid TEXT,
                title TEXT,
                url TEXT UNIQUE,
                geoHash TEXT,
                type TEXT,
                typology_id INTEGER,
                typology_name TEXT,
                contract TEXT,
                isNew BOOLEAN,
                luxury BOOLEAN,
                visibility BOOLEAN,
                isProjectLike BOOLEAN,
                isMosaic BOOLEAN,
                propertiesCount INTEGER,
                price_value REAL,
                price_formatted TEXT,
                price_min REAL,
                price_max REAL,
                price_range TEXT,
                price_visible BOOLEAN,
                surface TEXT,
                surface_m2 INTEGER,
                rooms INTEGER,
                bathrooms INTEGER,
                floor TEXT,
                floor_number INTEGER,
                floor_ga4value TEXT,
                elevator BOOLEAN,
                address TEXT,
                latitude REAL,
                longitude REAL,
                city TEXT,
                province TEXT,
                region TEXT,
                macrozone TEXT,
                nation TEXT,
                description TEXT,
                caption TEXT,
                ga4features TEXT,
                ga4Heating TEXT,
                ga4Garage TEXT,
                views TEXT,
                agency_id INTEGER,
                agency_type TEXT,
                agency_name TEXT,
                agency_label TEXT,
                agency_url TEXT,
                photo_id TEXT,
                photo_caption TEXT,
                photo_url_small TEXT,
                photo_url_medium TEXT,
                photo_url_large TEXT,
                typologyGA4Translation TEXT,
                matchSearch TEXT,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create index on url for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON real_estate_ads(url)')
            
            # Create trigger to update the updated_at field
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_timestamp
            AFTER UPDATE ON real_estate_ads
            FOR EACH ROW
            BEGIN
                UPDATE real_estate_ads SET updated_at = CURRENT_TIMESTAMP
                WHERE id = OLD.id;
            END;
            ''')
            
            conn.commit()
            logger.info(f"Successfully initialized database at {db_path}")
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        return False


def transform_df_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform DataFrame column data types to appropriate types for SQLite.
    
    Args:
        df: DataFrame containing real estate ads
        
    Returns:
        DataFrame with transformed data types
    """
    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()
    
    # Transform integer columns
    integer_columns = [
        'id', 'typology_id', 'propertiesCount', 'rooms', 'bathrooms', 'agency_id'
    ]
    
    for col in integer_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')  # Int64 can handle NaN
    
    # Transform float columns
    float_columns = [
        'price_value', 'price_min', 'price_max', 'latitude', 'longitude'
    ]
    
    for col in float_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Special transformations for specific columns
    
    # Extract numeric values from surface (e.g. "120 m²" -> 120)
    if 'surface' in df.columns:
        if df['surface'].dtype == 'object':
            # Extract numbers from string
            df['surface_m2'] = df['surface'].str.extract(r'(\d+)', expand=False)
            df['surface_m2'] = pd.to_numeric(df['surface_m2'], errors='coerce').astype('Int64')
    
    # Convert floor_number, handling special cases
    if 'floor_number' in df.columns:
        # Handle text floor descriptions
        if df['floor_number'].dtype == 'object':
            floor_mapping = {
                'piano terra': 0, 
                'terra': 0, 
                'piano rialzato': 0, 
                'rialzato': 0,
                'seminterrato': -1,
                'interrato': -1,
                'terra/rialzato': 0,
                'ammezzato': 1
            }
            
            # Apply mapping for text values first
            for text, value in floor_mapping.items():
                df.loc[df['floor_number'].str.contains(text, case=False, na=False), 'floor_number'] = value
            
            # Now convert to numeric
            df['floor_number'] = pd.to_numeric(df['floor_number'], errors='coerce').astype('Int64')
    
    # Convert boolean columns (ensure we handle all types of boolean representations)
    boolean_columns = ['isNew', 'luxury', 'visibility', 'isProjectLike', 'isMosaic', 
                      'price_visible', 'elevator']
                      
    # Comprehensive mapping for boolean values
    bool_mapping = {
        # String values (case-insensitive)
        'true': True, 'false': False,
        'yes': True, 'no': False,
        'y': True, 'n': False,
        't': True, 'f': False,
        'sì': True, 'si': True,
        's': True,
        # Italian values
        'vero': True, 'falso': False,
        # Numeric values
        '1': True, '0': False,
        1: True, 0: False
    }
    
    for col in boolean_columns:
        if col in df.columns:
            # Convert all string values to lowercase for case-insensitive mapping
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.lower()
                # Apply the mapping
                df[col] = df[col].map({k.lower() if isinstance(k, str) else k: v 
                                      for k, v in bool_mapping.items()})
    
    # Clean up text fields
    text_columns = [
        'title', 'description', 'address', 'caption', 'ga4features', 'ga4Heating', 
        'ga4Garage', 'views', 'city', 'province', 'region', 'macrozone', 'nation',
        'agency_name', 'agency_label', 'agency_url', 'photo_caption', 'typologyGA4Translation'
    ]
    
    for col in text_columns:
        if col in df.columns and df[col].dtype == 'object':
            # Remove extra whitespace and normalize
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
            # Replace 'nan' or 'None' strings with actual None
            df[col] = df[col].replace({'nan': None, 'None': None, 'null': None})
    
    # URL columns should be properly formatted
    url_columns = ['url', 'agency_url', 'photo_url_small', 'photo_url_medium', 'photo_url_large']
    for col in url_columns:
        if col in df.columns and df[col].dtype == 'object':
            # Trim whitespace
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' or 'None' strings with actual None
            df[col] = df[col].replace({'nan': None, 'None': None, 'null': None})
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    return df


def clean_df_from_sqlite(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the DataFrame loaded from SQLite.
    This function can be used after read_ads_from_sqlite to clean and convert data.
    
    Args:
        df: DataFrame loaded from SQLite
        
    Returns:
        Cleaned DataFrame with proper data types
    """
    if df.empty:
        return df
        
    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()
    
    # Convert integer columns
    integer_columns = {
        'id': 'Int64',                   # Use Int64 for columns that might contain NULLs
        'typology_id': 'Int64',
        'propertiesCount': 'Int64',
        'surface_m2': 'Int64',
        'rooms': 'Int64',
        'bathrooms': 'Int64',
        'floor_number': 'Int64',
        'agency_id': 'Int64'
    }
    
    # Apply integer conversions
    for col, dtype in integer_columns.items():
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(dtype)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not convert column {col} to {dtype}: {e}")
    
    # Convert float columns
    float_columns = {
        'price_value': float,
        'price_min': float,
        'price_max': float,
        'latitude': float,
        'longitude': float
    }
    
    # Apply float conversions
    for col, convert_func in float_columns.items():
        if col in df.columns:
            try:
                df[col] = df[col].apply(lambda x: None if pd.isna(x) else convert_func(x))
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not convert column {col} to float: {e}")
    
    # Convert boolean columns
    bool_columns = [
        'isNew', 'luxury', 'visibility', 'isProjectLike', 'isMosaic',
        'elevator', 'price_visible'
    ]
    
    # Comprehensive mapping for boolean values
    bool_map = {
        # String values (case-insensitive)
        'true': True, 'false': False,
        'yes': True, 'no': False,
        'y': True, 'n': False,
        't': True, 'f': False,
        'sì': True, 'si': True,
        's': True,
        # Italian values
        'vero': True, 'falso': False,
        # Numeric values
        '1': True, '0': False,
        1: True, 0: False,
        # Handle SQLite's specific boolean storage
        1.0: True, 0.0: False
    }
    
    for col in bool_columns:
        if col in df.columns:
            try:
                # Handle various boolean formats
                if df[col].dtype == 'object':
                    # Convert string values to lowercase for case-insensitive mapping
                    df[col] = df[col].astype(str).str.lower()
                    # Apply the mapping
                    df[col] = df[col].map({k.lower() if isinstance(k, str) else k: v 
                                        for k, v in bool_map.items()})
                elif df[col].dtype in ('int64', 'float64'):
                    # Convert numeric to boolean
                    df[col] = df[col].map({1: True, 0: False, 1.0: True, 0.0: False})
            except Exception as e:
                logger.warning(f"Could not convert boolean column {col}: {e}")
    
    # Clean up text fields
    text_columns = [
        'title', 'description', 'address', 'caption', 'ga4features', 'ga4Heating', 
        'ga4Garage', 'views', 'city', 'province', 'region', 'macrozone', 'nation',
        'agency_name', 'agency_label', 'agency_type', 'photo_caption', 'typologyGA4Translation',
        'matchSearch', 'contract', 'type', 'typology_name', 'geoHash'
    ]
    
    for col in text_columns:
        if col in df.columns and df[col].dtype == 'object':
            try:
                # Replace NaN with None
                df[col] = df[col].replace({pd.NA: None, 'nan': None, 'None': None, 'null': None})
                # Only process non-null values
                mask = df[col].notna()
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
            except Exception as e:
                logger.warning(f"Could not clean text column {col}: {e}")
    
    # Process URL fields
    url_columns = [
        'url', 'agency_url', 'photo_url_small', 'photo_url_medium', 'photo_url_large'
    ]
    
    for col in url_columns:
        if col in df.columns and df[col].dtype == 'object':
            try:
                # Replace NaN with None
                df[col] = df[col].replace({pd.NA: None, 'nan': None, 'None': None, 'null': None})
                # Only process non-null values
                mask = df[col].notna()
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
            except Exception as e:
                logger.warning(f"Could not clean URL column {col}: {e}")
    
    # Format price columns
    price_text_columns = ['price_formatted', 'price_range']
    for col in price_text_columns:
        if col in df.columns and df[col].dtype == 'object':
            try:
                # Only process non-null values
                mask = df[col].notna()
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
            except Exception as e:
                logger.warning(f"Could not clean price text column {col}: {e}")
    
    # Parse date columns
    date_columns = ['created_at', 'updated_at']
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception as e:
                logger.warning(f"Could not convert date column {col}: {e}")
    
    return df


def write_df_to_sqlite(df: pd.DataFrame, db_path: str, replace_existing: bool = False) -> Tuple[int, int]:
    """
    Write a DataFrame of real estate ads to the SQLite database.
    
    Args:
        df: DataFrame containing real estate ads
        db_path: Path to the SQLite database file
        replace_existing: Whether to replace existing records with the same URL
        
    Returns:
        Tuple of (number of new records, number of updated records)
    """
    try:
        # Initialize the database if it doesn't exist
        if not os.path.exists(db_path):
            init_database(db_path)
            
        new_records = 0
        updated_records = 0
            
        with get_connection(db_path) as conn:
            # Prepare a cursor to check if the database schema has all needed columns
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(real_estate_ads)")
            existing_columns = {column[1] for column in cursor.fetchall()}
            
            # Transform DataFrame dtypes
            df = transform_df_dtypes(df)
            
            # # Define all column groups based on the provided structure
            # column_groups = [
            #     # Identificazione
            #     ["id", "uuid", "title", "url", "geoHash"],
            #     # Tipo e visibilità
            #     ["type", "typology_id", "typology_name", "contract", "isNew", "luxury", "visibility", "isProjectLike", "isMosaic", "propertiesCount"],
            #     # Prezzo
            #     [col for col in df.columns if col.startswith("price_")],
            #     # Caratteristiche principali
            #     ["surface", "surface_m2", "rooms", "bathrooms", "floor", "floor_number", "floor_ga4value", "elevator"],
            #     # Posizione
            #     ["address", "latitude", "longitude", "city", "province", "region", "macrozone", "nation", "zone"],
            #     # Descrizioni e caratteristiche
            #     ["description", "caption", "ga4features", "ga4Heating", "ga4Garage", "views", 
            #      "property_type", "kitchen", "furnished", "terrace", "ac_type", "contract_type", 
            #      "building_floors", "bedrooms", "balcony", "heating_type", "other_features"],
            #     # Agenzia
            #     [col for col in df.columns if col.startswith("agency_")],
            #     # Foto
            #     [col for col in df.columns if col.startswith("photo_")]
            # ]
            #   # Add any columns from the original DataFrame that weren't in our groups
            # flat_groups = [item for sublist in column_groups for item in sublist if isinstance(item, str)]
            # remaining_columns = [col for col in df.columns if col not in flat_groups]
            
            # # Also map any old column names to new schema
            # column_mapping = {
            #     'titolo': 'title',
            #     'descrizione': 'description',
            #     'indirizzo': 'address',
            #     'comune': 'city',
            #     'provincia': 'province',
            #     'zona': 'zone',
            #     'tipologia': 'property_type',
            #     'piano': 'floor',
            #     'ascensore': 'elevator',
            #     'locali': 'rooms',
            #     'cucina': 'kitchen',
            #     'arredato': 'furnished',
            #     'terrazzo': 'terrace',
            #     'climatizzazione': 'ac_type',
            #     'contratto': 'contract_type',
            #     'piani_edificio': 'building_floors',
            #     'superficie': 'surface',
            #     'camere_da_letto': 'bedrooms',
            #     'bagni': 'bathrooms',
            #     'balcone': 'balcony',
            #     'riscaldamento': 'heating_type',
            #     'altre_caratteristiche': 'other_features',
            #     'prezzo': 'price',
            #     'prezzo_al_mq': 'price_per_sqm',
            #     'spese_condominio': 'condo_fees',
            #     'cauzione': 'deposit',
            #     'consumo_di_energia': 'energy_consumption'
            # }
            
            # # Rename columns if they are in the old format
            # for old_col, new_col in column_mapping.items():
            #     if old_col in df.columns and new_col not in df.columns:
            #         df = df.rename(columns={old_col: new_col})
            
            # # Check if we need to add new columns to the schema
            # all_columns = list(df.columns)
            # missing_columns = [col for col in all_columns if col not in existing_columns]
            
            # if missing_columns:
            #     # Determine type for new columns
            #     for col in missing_columns:
            #         # Determine SQLite data type based on pandas dtype
            #         col_type = 'TEXT'  # Default
            #         if col in df.columns:
            #             dtype = str(df[col].dtype)
            #             if 'int' in dtype:
            #                 col_type = 'INTEGER'
            #             elif 'float' in dtype:
            #                 col_type = 'REAL'
            #             elif dtype == 'bool':
            #                 col_type = 'BOOLEAN'
                    
            #         cursor.execute(f"ALTER TABLE real_estate_ads ADD COLUMN {col} {col_type}")
            #     conn.commit()
            #     logger.info(f"Added new columns to schema: {missing_columns}")
            
            # Add raw_data column with the entire row as JSON if not present
            if 'raw_data' not in df.columns:
                df['raw_data'] = df.apply(lambda row: json.dumps(row.to_dict(), ensure_ascii=False), axis=1)
            
            # Insert each row individually to handle duplicate URLs properly
            for _, row in df.iterrows():
                if 'url' not in row or pd.isna(row['url']):
                    logger.warning(f"Skipping record with missing URL: {row.get('title', 'Unknown')}")
                    continue
                    
                # Check if the URL already exists
                cursor.execute("SELECT id FROM real_estate_ads WHERE url = ?", (row['url'],))
                existing_record = cursor.fetchone()
                
                # Filter out NaN values and non-existent columns
                valid_columns = [col for col in row.index if col in existing_columns and not (pd.isna(row[col]) and col != 'url')]
                valid_values = [row[col] for col in valid_columns]
                
                if existing_record and replace_existing:
                    # Update existing record
                    set_clauses = [f"{col} = ?" for col in valid_columns if col != 'url']
                    set_values = [row[col] for col in valid_columns if col != 'url']
                    
                    if set_clauses:  # Only proceed if there are columns to update
                        cursor.execute(
                            f"UPDATE real_estate_ads SET {', '.join(set_clauses)} WHERE url = ?",
                            set_values + [row['url']]
                        )
                        updated_records += 1
                    
                elif not existing_record:
                    # Insert new record
                    placeholders = ", ".join(["?"] * len(valid_columns))
                    column_names = ", ".join(valid_columns)
                    
                    cursor.execute(
                        f"INSERT INTO real_estate_ads ({column_names}) VALUES ({placeholders})",
                        valid_values
                    )
                    new_records += 1
            
            conn.commit()
            logger.info(f"Wrote {new_records} new records and updated {updated_records} existing records to database")
            return new_records, updated_records
            
    except (sqlite3.Error, pd.errors.EmptyDataError) as e:
        logger.error(f"Error writing to database: {e}")
        return 0, 0


def read_ads_from_sqlite(
    db_path: str, 
    filters: Optional[Dict[str, Any]] = None, 
    order_by: str = "created_at DESC",
    limit: Optional[int] = None,
    clean_data: bool = True
) -> pd.DataFrame:
    """
    Read real estate ads from the SQLite database with optional filters.
    
    Args:
        db_path: Path to the SQLite database file
        filters: Dictionary of column name to filter value
        order_by: Column to sort by, with optional ASC/DESC
        limit: Maximum number of records to return
        clean_data: Whether to clean and transform the loaded data
        
    Returns:
        DataFrame containing the requested records
    """
    try:
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return pd.DataFrame()
            
        with get_connection(db_path) as conn:
            query = "SELECT * FROM real_estate_ads"
            params = []
            
            if filters:
                conditions = []
                for column, value in filters.items():
                    if isinstance(value, (list, tuple)):
                        placeholders = ", ".join(["?"] * len(value))
                        conditions.append(f"{column} IN ({placeholders})")
                        params.extend(value)
                    else:
                        conditions.append(f"{column} = ?")
                        params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            if order_by:
                query += f" ORDER BY {order_by}"
                
            if limit is not None:
                query += f" LIMIT {limit}"
                df = pd.read_sql_query(query, conn, params=params)
            logger.info(f"Retrieved {len(df)} records from database")
            
            if clean_data and not df.empty:
                df = clean_df_from_sqlite(df)
                logger.info("Data cleaning and transformation applied")
                
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Error reading from database: {e}")
        return pd.DataFrame()


def search_ads_by_text(
    db_path: str,
    search_text: str,
    search_columns: List[str] = ['title', 'description', 'address', 'zone', 'city'],
    order_by: str = "created_at DESC",
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Search for real estate ads containing specific text in the specified columns.
    
    Args:
        db_path: Path to the SQLite database file
        search_text: Text to search for
        search_columns: List of columns to search in
        order_by: Column to sort by, with optional ASC/DESC
        limit: Maximum number of records to return
        
    Returns:
        DataFrame containing the matching records
    """
    try:
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return pd.DataFrame()
            
        with get_connection(db_path) as conn:
            conditions = []
            params = []
            
            for column in search_columns:
                conditions.append(f"{column} LIKE ?")
                params.append(f"%{search_text}%")
                
            query = f"SELECT * FROM real_estate_ads WHERE {' OR '.join(conditions)}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
                
            if limit is not None:
                query += f" LIMIT {limit}"
                
            df = pd.read_sql_query(query, conn, params=params)
            logger.info(f"Found {len(df)} records matching '{search_text}'")
            return df
            
    except sqlite3.Error as e:
        logger.error(f"Error searching database: {e}")
        return pd.DataFrame()


def delete_ads_by_url(db_path: str, urls: List[str]) -> int:
    """
    Delete real estate ads with the specified URLs.
    
    Args:
        db_path: Path to the SQLite database file
        urls: List of URLs to delete
        
    Returns:
        Number of records deleted
    """
    try:
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return 0
            
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            placeholders = ", ".join(["?"] * len(urls))
            cursor.execute(f"DELETE FROM real_estate_ads WHERE url IN ({placeholders})", urls)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Deleted {deleted_count} records from database")
            return deleted_count
            
    except sqlite3.Error as e:
        logger.error(f"Error deleting from database: {e}")
        return 0


def get_database_stats(db_path: str) -> Dict[str, Any]:
    """
    Get statistics about the real estate ads database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        Dictionary containing database statistics
    """
    try:
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return {}
            
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Total number of records
            cursor.execute("SELECT COUNT(*) FROM real_estate_ads")
            total_records = cursor.fetchone()[0]
            
            # Records by property type
            cursor.execute("""
                SELECT property_type, COUNT(*) as count 
                FROM real_estate_ads 
                GROUP BY property_type 
                ORDER BY count DESC
            """)
            property_types = {row['property_type']: row['count'] for row in cursor.fetchall()}
            
            # Records by city
            cursor.execute("""
                SELECT city, COUNT(*) as count 
                FROM real_estate_ads 
                WHERE city IS NOT NULL
                GROUP BY city 
                ORDER BY count DESC
                LIMIT 10
            """)
            cities = {row['city']: row['count'] for row in cursor.fetchall()}
            
            # Average price by property type
            cursor.execute("""
                SELECT property_type, AVG(CAST(REPLACE(REPLACE(price, '€', ''), '.', '') AS NUMERIC)) as avg_price
                FROM real_estate_ads 
                WHERE price NOT LIKE '%/mese%'
                GROUP BY property_type
            """)
            avg_prices = {row['property_type']: row['avg_price'] for row in cursor.fetchall()}
            
            # Most recent record
            cursor.execute("""
                SELECT created_at 
                FROM real_estate_ads 
                ORDER BY created_at DESC
                LIMIT 1
            """)
            latest_record = cursor.fetchone()
            latest_date = latest_record['created_at'] if latest_record else None
            
            stats = {
                "total_records": total_records,
                "property_types": property_types,
                "top_cities": cities,
                "average_prices": avg_prices,
                "latest_record_date": latest_date,
                "database_path": db_path,
                "stats_generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Generated database statistics for {db_path}")
            return stats
            
    except sqlite3.Error as e:
        logger.error(f"Error getting database statistics: {e}")
        return {}


def export_to_csv(
    db_path: str,
    output_path: str,
    filters: Optional[Dict[str, Any]] = None,
    order_by: str = "created_at DESC"
) -> bool:
    """
    Export data from the SQLite database to a CSV file.
    
    Args:
        db_path: Path to the SQLite database file
        output_path: Path to save the CSV file
        filters: Dictionary of column name to filter value
        order_by: Column to sort by, with optional ASC/DESC
        
    Returns:
        True if export was successful, False otherwise
    """
    try:
        df = read_ads_from_sqlite(db_path, filters, order_by)
        
        if df.empty:
            logger.warning("No records found to export")
            return False
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(df)} records to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    pass
