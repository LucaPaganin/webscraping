#!/usr/bin/env python3
"""
Real Estate Data Collection CLI
==============================

Command-line interface for the object-oriented real estate data collection system.

Author: Lucas P
Date: July 6, 2025
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

from config import setup_logging, load_configuration, validate_configuration
from retrievers import ImmobiliareAdRetriever
from data_manager import RealEstateDataManager


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
    basic_group.add_argument('--max-pages', '-m', type=lambda x: int(x) if x != '0' else None, default=1,
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
  python main.py --city genova --list-zones
  
  # Fetch rental ads for Genova (1 page only)
  python main.py --city genova --contract rent
  
  # Fetch all rental ads for Genova
  python main.py --city genova --contract rent --max-pages 0
  
  # Fetch all sale ads for Genova, zone by zone
  python main.py --city genova --contract sale --max-pages 0 --use-zones --region lig
  
  # Fetch ads only for specific macrozones using IDs
  python main.py --city genova --macrozones 13297 13298
  
  # Save results to multiple formats
  python main.py --city genova --save-csv --save-json --save-sqlite --output-path ./data
'''
    
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    try:
        # Parse arguments and setup logging
        args = parse_arguments()
        logger = setup_logging(args.log_to_file)
        
        logger.info("=== Real Estate Data Collection System ===")
        logger.info(f"Target city: {args.city}")
        logger.info(f"Contract type: {args.contract}")
        logger.info(f"Max pages: {args.max_pages if args.max_pages else 'all'}")
        
        # Load and validate configuration
        config = load_configuration()
        config = validate_configuration(config)
        
        # Add command-line arguments to config
        config.update({
            'contract_type': args.contract,
            'region': args.region
        })
        
        # Create retriever instance (currently only Immobiliare)
        retriever = ImmobiliareAdRetriever(config)
        
        # Handle list-zones command
        if args.list_zones:
            data_manager = RealEstateDataManager(retriever, config)
            data_manager.list_zones(args.city)
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
            'delay_range': (config.get('request_delay_min', 2.5), config.get('request_delay_max', 5.0))
        }
        
        # Collect ads
        logger.info("Starting data collection...")
        ads = data_manager.collect_ads(**search_params)
        
        if not ads:
            logger.warning("No ads were collected")
            return
        
        logger.info(f"Successfully collected {len(ads)} ads")
        
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
        
        # Save results
        logger.info("Saving results...")
        save_results = data_manager.save_ads(ads, output_config)
        
        # Report save results
        for format_name, success in save_results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {format_name.upper()}: {'Success' if success else 'Failed'}")
        
        # Summary
        successful_saves = sum(save_results.values())
        total_formats = len(save_results)
        
        if successful_saves > 0:
            logger.info(f"=== Collection completed successfully! ===")
            logger.info(f"Ads collected: {len(ads)}")
            logger.info(f"Formats saved: {successful_saves}/{total_formats}")
        else:
            logger.error("Failed to save data in any format")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
