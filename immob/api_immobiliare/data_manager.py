#!/usr/bin/env python3
"""
Real Estate Data Manager
========================

Manager class for handling real estate data operations including collection and storage.

Author: Lucas P
Date: July 6, 2025
"""

import json
import logging
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from real_estate_models import RealEstateAd
from retrievers import RealEstateAdRetriever
from helpers import init_cosmos_client, transform_df_dtypes
from sqlite_helpers import write_df_to_sqlite, init_database


class RealEstateDataManager:
    """
    Manager class for handling real estate data operations.
    
    This class coordinates data retrieval, processing, and storage operations.
    It uses composition with a RealEstateAdRetriever to fetch data and provides
    methods for saving to various formats.
    """
    
    def __init__(self, retriever: RealEstateAdRetriever, config: Dict[str, Any]):
        """
        Initialize the data manager.
        
        Args:
            retriever: Instance of RealEstateAdRetriever for data collection
            config: Configuration dictionary
        """
        self.retriever = retriever
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def collect_ads(self, **search_params) -> List[RealEstateAd]:
        """
        Collect ads using the configured retriever.
        
        Args:
            **search_params: Search parameters to pass to the retriever
            
        Returns:
            List of collected RealEstateAd instances
        """
        use_zones = search_params.get('use_zones', False)
        city = search_params.get('city')
        
        if use_zones and city:
            self.logger.info(f"Collecting ads by zones for city: {city}")
            zone_ads = self.retriever.fetch_by_zones(city, **search_params)
            
            # Flatten zone-based results
            all_ads = []
            for zone_name, ads in zone_ads.items():
                all_ads.extend(ads)
            
            return all_ads
        else:
            self.logger.info("Collecting ads with single query")
            return self.retriever.fetch_ads(**search_params)
    
    def save_to_csv(self, ads: List[RealEstateAd], filename: str) -> bool:
        """
        Save ads to CSV format.
        
        Args:
            ads: List of RealEstateAd instances
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not ads:
                self.logger.warning("No ads to save to CSV")
                return False
            
            # Convert ads to DataFrame
            ads_data = [ad.to_dict() for ad in ads]
            df = pd.DataFrame(ads_data)
            
            # Transform data types for better CSV compatibility
            df = transform_df_dtypes(df)
            
            # Ensure output directory exists
            output_path = Path(filename).parent
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            self.logger.info(f"Saved {len(ads)} ads to CSV: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
            return False
    
    def save_to_json(self, ads: List[RealEstateAd], filename: str) -> bool:
        """
        Save ads to JSON format.
        
        Args:
            ads: List of RealEstateAd instances
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not ads:
                self.logger.warning("No ads to save to JSON")
                return False
            
            # Convert ads to dictionaries
            ads_data = [ad.to_dict() for ad in ads]
            
            # Ensure output directory exists
            output_path = Path(filename).parent
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON with proper datetime serialization
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(ads_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Saved {len(ads)} ads to JSON: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
            return False
    
    def save_to_sqlite(self, ads: List[RealEstateAd], db_path: str, table_name: str = 'ads') -> bool:
        """
        Save ads to SQLite database.
        
        Args:
            ads: List of RealEstateAd instances
            db_path: Path to SQLite database file
            table_name: Name of the table to create/use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not ads:
                self.logger.warning("No ads to save to SQLite")
                return False
            
            # Convert ads to DataFrame
            ads_data = [ad.to_dict() for ad in ads]
            df = pd.DataFrame(ads_data)
            
            # Transform data types for database compatibility
            df = transform_df_dtypes(df)
            
            # Ensure output directory exists
            output_path = Path(db_path).parent
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize database if needed
            init_database(db_path)
            
            # Write to SQLite
            write_df_to_sqlite(df, db_path, table_name)
            self.logger.info(f"Saved {len(ads)} ads to SQLite: {db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to SQLite: {e}")
            return False
    
    def save_to_cosmos_db(self, ads: List[RealEstateAd], container_name: str) -> bool:
        """
        Save ads to Azure Cosmos DB.
        
        Args:
            ads: List of RealEstateAd instances
            container_name: Name of the Cosmos DB container
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not ads:
                self.logger.warning("No ads to save to Cosmos DB")
                return False
            
            # Initialize Cosmos DB client
            cosmos_client = init_cosmos_client(
                self.config.get('cosmos_endpoint', ''),
                self.config.get('cosmos_key', ''),
                self.config.get('cosmos_db', '')
            )
            
            if not cosmos_client:
                self.logger.error("Failed to initialize Cosmos DB client")
                return False
            
            # Get container
            database = cosmos_client.get_database_client(self.config.get('cosmos_db'))
            container = database.get_container_client(container_name)
            
            # Upload ads
            successful_uploads = 0
            for ad in ads:
                try:
                    ad_dict = ad.to_dict()
                    # Ensure id field is string for Cosmos DB
                    ad_dict['id'] = str(ad_dict['id'])
                    container.upsert_item(ad_dict)
                    successful_uploads += 1
                except Exception as e:
                    self.logger.warning(f"Failed to upload ad {ad.id}: {e}")
                    continue
            
            self.logger.info(f"Saved {successful_uploads}/{len(ads)} ads to Cosmos DB: {container_name}")
            return successful_uploads > 0
            
        except Exception as e:
            self.logger.error(f"Error saving to Cosmos DB: {e}")
            return False
    
    def save_ads(self, ads: List[RealEstateAd], output_config: Dict[str, Any]) -> Dict[str, bool]:
        """
        Save ads to multiple formats based on configuration.
        
        Args:
            ads: List of RealEstateAd instances
            output_config: Configuration specifying output formats and settings
            
        Returns:
            Dictionary mapping format names to success status
        """
        results = {}
        
        if not ads:
            self.logger.warning("No ads to save")
            return results
        
        # Extract configuration
        output_path = Path(output_config.get('output_path', '.'))
        city = output_config.get('city', 'unknown')
        contract_type = output_config.get('contract_type', 'rent')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Base filename
        base_filename = f"{city}_{contract_type}_{timestamp}"
        
        # Save to CSV
        if output_config.get('save_to_csv', True):
            csv_filename = output_path / f"{base_filename}.csv"
            results['csv'] = self.save_to_csv(ads, str(csv_filename))
        
        # Save to JSON
        if output_config.get('save_to_json', False):
            json_filename = output_path / f"{base_filename}.json"
            results['json'] = self.save_to_json(ads, str(json_filename))
        
        # Save to SQLite
        if output_config.get('save_to_sqlite', False):
            sqlite_path = output_config.get('sqlite_path')
            if not sqlite_path:
                sqlite_path = output_path / "ads.db"
            results['sqlite'] = self.save_to_sqlite(ads, str(sqlite_path))
        
        # Save to Cosmos DB
        if output_config.get('save_to_cosmos', False):
            container_name = output_config.get('cosmos_container')
            if not container_name:
                container_name = f"ads_{contract_type}"
            results['cosmos'] = self.save_to_cosmos_db(ads, container_name)
        
        return results
    
    def list_zones(self, city: str) -> None:
        """
        List available zones for a city.
        
        Args:
            city: City name
        """
        zones_data = self.retriever.get_city_zones(city)
        
        if not zones_data:
            print(f"No zone data found for city: {city}")
            return
        
        print(f"\nAvailable zones for {city.capitalize()}:")
        print("=" * 50)
        
        # Display general city information
        if 'idComune' in zones_data:
            print(f"Comune ID: {zones_data['idComune']}")
        if 'name' in zones_data:
            print(f"Comune Name: {zones_data['name']}")
        
        # Display macrozones
        macrozones = zones_data.get('macrozones', {})
        if macrozones:
            print(f"\nMacrozones ({len(macrozones)}):")
            print("-" * 30)
            for macro_id, macro_info in macrozones.items():
                print(f"  {macro_id}: {macro_info.get('name', 'Unknown')}")
        
        # Display zones
        zones = zones_data.get('zones', {})
        if zones:
            print(f"\nZones ({len(zones)}):")
            print("-" * 20)
            for zone_id, zone_info in zones.items():
                zone_name = zone_info.get('name', 'Unknown')
                macro_id = zone_info.get('macrozone_id', 'N/A')
                print(f"  {zone_id}: {zone_name} (Macrozone: {macro_id})")
        
        if not macrozones and not zones:
            print("No zones or macrozones found for this city.")
