#!/usr/bin/env python3
"""
Real Estate Data Retrieval CLI
==============================

Command-line interface for the real estate data retrieval system.
This is the main entry point for using the system from the command line.

Author: Lucas P
Date: July 6, 2025
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

from config import setup_logging, load_configuration
from retrievers import ImmobiliareAdRetriever
from data_manager import RealEstateDataManager
from real_estate_models import RealEstateAd


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='''
        Object-Oriented Real Estate Data Retrieval System
        =================================================
        
        Fetch real estate ads from various websites using an extensible OOP architecture.
        Currently supports immobiliare.it with zone-by-zone processing capabilities.
        
        Processing modes:
        1. Single query mode: Fetches all ads in one query (default)
        2. Zone-by-zone mode: Fetches ads for each zone separately (--use-zones)
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
                         help='Path to SQLite database file (default: output-path/ads.db)')
    output_group.add_argument('--save-cosmos', action='store_true', default=False,
                         help='Save data to Cosmos DB (requires proper .env configuration)')
    output_group.add_argument('--cosmos-container', type=str, default=None,
                         help='Cosmos DB container name (default: ads_<contract_type>)')
    
    # Add examples section
    parser.epilog = '''
Examples:
  # List available zones for Genova
  python fetch_ads_cli.py --city genova --list-zones
  
  # Fetch rental ads for Genova (1 page only)
  python fetch_ads_cli.py --city genova --contract rent
  
  # Fetch all rental ads for Genova
  python fetch_ads_cli.py --city genova --contract rent --max-pages 0
  
  # Fetch all sale ads for Genova, zone by zone
  python fetch_ads_cli.py --city genova --contract sale --max-pages 0 --use-zones --region lig
  
  # Fetch ads only for specific macrozones using IDs
  python fetch_ads_cli.py --city genova --macrozones 13297 13298
  
  # Save results to multiple formats
  python fetch_ads_cli.py --city genova --save-csv --save-json --save-sqlite --output-path ./data
'''
    
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    # Parse arguments and setup logging
    args = parse_arguments()
    logger = setup_logging(args.log_to_file)
    
    # Load configuration
    config = load_configuration()
    
    # Add command-line arguments to config
    config.update({
        'contract_type': args.contract,
        'region': args.region
    })
    
    # Create retriever instance (currently only Immobiliare)
    retriever = ImmobiliareAdRetriever(config)
    
    # Handle list-zones command
    if args.list_zones:
        zones = retriever.get_city_zones(args.city)
        if zones:
            logger.info(f"Available zones for {args.city.capitalize()}:")
            for zone_id, zone_info in zones.get('zones', {}).items():
                logger.info(f"  - {zone_info.get('name', 'Unknown')} (ID: {zone_info.get('id', 'Unknown')})")
            
            logger.info(f"\nAvailable macrozones for {args.city.capitalize()}:")
            for zone_id, zone_info in zones.get('macrozones', {}).items():
                logger.info(f"  - {zone_info.get('name', 'Unknown')} (ID: {zone_info.get('id', 'Unknown')})")
        else:
            logger.warning(f"No zones found for {args.city}")
        return
    
    # Create data manager
    data_manager = RealEstateDataManager(retriever, config)
    
    # Prepare search parameters
    search_params = {
        'city': args.city,
        'contract_type': args.contract,
        'region': args.region,
        'max_pages': args.max_pages,
        'start_page': args.start_page,
        'use_zones': args.use_zones,
        'macrozones': args.macrozones,
        'delay_range': (2.5, 5.0)
    }
    
    # Prepare output configuration
    output_config = {
        'output_path': args.output_path,
        'city': args.city,
        'contract_type': args.contract,
        'save_to_csv': args.save_csv,
        'save_to_json': args.save_json,
        'save_to_sqlite': args.save_sqlite,
        'sqlite_path': args.sqlite_path,
        'save_to_cosmos': args.save_cosmos,
        'cosmos_container': args.cosmos_container
    }
    
    # Collect ads
    if args.use_zones:
        logger.info(f"Fetching ads zone-by-zone for {args.city.capitalize()}, contract type: {args.contract}")
        ads_by_zone = retriever.fetch_by_zones(**search_params)
        
        # Save each zone separately
        for zone_name, zone_ads in ads_by_zone.items():
            if not zone_ads:
                logger.warning(f"No ads found for zone: {zone_name}")
                continue
                
            zone_output = output_config.copy()
            zone_output['zone_name'] = zone_name
            data_manager.save_ads(zone_ads, zone_output)
        
        # Combine all ads for a full dataset
        all_ads = []
        for zone_ads in ads_by_zone.values():
            all_ads.extend(zone_ads)
            
        if all_ads:
            logger.info(f"Saving combined dataset with {len(all_ads)} ads from all zones")
            data_manager.save_ads(all_ads, output_config)
        else:
            logger.warning(f"No ads found for any zone in {args.city}")
    else:
        logger.info(f"Fetching ads for {args.city.capitalize()}, contract type: {args.contract}")
        ads = data_manager.collect_ads(**search_params)
        
        if ads:
            logger.info(f"Saving dataset with {len(ads)} ads")
            data_manager.save_ads(ads, output_config)
        else:
            logger.warning(f"No ads found for {args.city}")
    
    logger.info("Done!")


if __name__ == "__main__":
    main()
