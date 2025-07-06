#!/usr/bin/env python3
"""
Real Estate Data Upload Tool
===========================

Utility for uploading CSV data to various storage destinations using the RealEstateDataManager.
Supports uploading to SQLite and Cosmos DB with detailed reporting and batch processing.

Author: Lucas P
Date: July 6, 2025
"""

import os
import sys
import json
import argparse
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union, Optional

# Import from our modules
from config import load_configuration, setup_logging
from data_manager import RealEstateDataManager
from retrievers import RealEstateAdRetriever
from real_estate_models import RealEstateAd
from helpers import transform_df_dtypes

# Setup logging
logger = setup_logging(log_level="INFO")

def find_csv_files(path_patterns: List[str]) -> List[Path]:
    """
    Find all CSV files matching the provided patterns.
    
    Args:
        path_patterns: List of file paths or directory paths to search
        
    Returns:
        List of Path objects for all matching CSV files
    """
    csv_files = []
    
    for pattern in path_patterns:
        path = Path(pattern)
        
        # If it's a directory, find all CSV files in it
        if path.is_dir():
            csv_files.extend(list(path.glob("*.csv")))
        # If it's a file, check if it's a CSV
        elif path.is_file() and path.suffix.lower() == '.csv':
            csv_files.append(path)
        # It might be a glob pattern
        else:
            matched_files = list(Path(".").glob(pattern))
            csv_files.extend([f for f in matched_files if f.is_file() and f.suffix.lower() == '.csv'])
    
    return csv_files

def load_csv_to_ads(csv_path: Union[str, Path]) -> List[RealEstateAd]:
    """
    Load a CSV file and convert to a list of RealEstateAd objects.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of RealEstateAd objects
    """
    logger.info(f"Loading CSV file: {csv_path}")
    
    try:
        # Load the CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} records from CSV")
        
        # Clean up the DataFrame
        df = transform_df_dtypes(df)
        
        # Convert to list of RealEstateAd objects
        ads = []
        for _, row in df.iterrows():
            try:
                # Convert row to dict and create RealEstateAd
                ad_dict = row.to_dict()
                ad = RealEstateAd.parse_obj(ad_dict)
                ads.append(ad)
            except Exception as e:
                logger.warning(f"Failed to parse row into RealEstateAd: {e}")
        
        logger.info(f"Successfully converted {len(ads)} records to RealEstateAd objects")
        return ads
        
    except Exception as e:
        logger.error(f"Error loading CSV file: {e}")
        return []

def upload_csv_with_batches(
    csv_path: Union[str, Path], 
    data_manager: RealEstateDataManager,
    output_format: str,
    batch_size: int = 50,
    **output_params
) -> Dict[str, Any]:
    """
    Upload CSV data in batches using the data manager.
    
    Args:
        csv_path: Path to the CSV file
        data_manager: RealEstateDataManager instance
        output_format: Format to save as ('csv', 'json', 'sqlite', 'cosmos')
        batch_size: Number of records per batch
        **output_params: Additional parameters for the specific output format
        
    Returns:
        Dictionary with upload statistics
    """
    results = {
        "file": str(csv_path),
        "output_format": output_format,
        "total_records": 0,
        "successful": 0,
        "failed": 0,
        "start_time": datetime.now(),
        "end_time": None,
        "errors": []
    }
    
    try:
        # Load all ads from CSV
        all_ads = load_csv_to_ads(csv_path)
        results["total_records"] = len(all_ads)
        
        if not all_ads:
            results["errors"].append("No valid records found in CSV")
            results["end_time"] = datetime.now()
            return results
        
        # Process in batches
        for i in range(0, len(all_ads), batch_size):
            batch = all_ads[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            logger.info(f"Processing batch {batch_num}/{(len(all_ads) + batch_size - 1) // batch_size} ({len(batch)} records)")
            
            # Save batch using appropriate method
            success = False
            try:
                if output_format == 'csv':
                    batch_filename = f"{output_params.get('filename', 'output')}_{batch_num}.csv"
                    success = data_manager.save_to_csv(batch, batch_filename)
                elif output_format == 'json':
                    batch_filename = f"{output_params.get('filename', 'output')}_{batch_num}.json"
                    success = data_manager.save_to_json(batch, batch_filename)
                elif output_format == 'sqlite':
                    success = data_manager.save_to_sqlite(
                        batch, 
                        output_params.get('db_path', 'real_estate.db'),
                        output_params.get('table_name', 'ads')
                    )
                elif output_format == 'cosmos':
                    success = data_manager.save_to_cosmos_db(
                        batch,
                        output_params.get('container_name', 'ads')
                    )
                
                if success:
                    results["successful"] += len(batch)
                    logger.info(f"Batch {batch_num} successfully saved ({len(batch)} records)")
                else:
                    results["failed"] += len(batch)
                    logger.warning(f"Failed to save batch {batch_num}")
                    results["errors"].append(f"Failed to save batch {batch_num}")
            
            except Exception as e:
                results["failed"] += len(batch)
                error_msg = f"Error processing batch {batch_num}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
    
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        logger.error(error_msg)
        results["errors"].append(error_msg)
    
    results["end_time"] = datetime.now()
    duration = results["end_time"] - results["start_time"]
    logger.info(f"Upload complete for {csv_path}: {results['successful']}/{results['total_records']} records successful")
    logger.info(f"Duration: {duration}")
    
    return results

def extract_metadata_from_filename(csv_path: Path) -> Dict[str, str]:
    """
    Extract metadata from the CSV filename.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary with extracted metadata
    """
    filename = csv_path.stem
    parts = filename.split('_')
    metadata = {}
    
    # Try to identify city and contract_type from filename patterns like:
    # - ads_genova_rent.csv
    # - genova_rent_20230101.csv
    # - milano_sale_apartments.csv
    
    if len(parts) >= 2:
        if parts[0] == 'ads' and len(parts) >= 3:
            metadata['city'] = parts[1]
            metadata['contract_type'] = parts[2]
        elif len(parts) >= 2:
            metadata['city'] = parts[0]
            if parts[1] in ['rent', 'sale']:
                metadata['contract_type'] = parts[1]
    
    logger.debug(f"Extracted metadata from filename: {metadata}")
    return metadata

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Upload CSV data to various destinations using RealEstateDataManager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload to SQLite
  python upload_data.py data/*.csv --sqlite data.db --table ads
  
  # Upload to Cosmos DB
  python upload_data.py data/*.csv --cosmos --container ads
  
  # Upload with custom batch size
  python upload_data.py data/large_file.csv --sqlite data.db --batch-size 100
  
  # Generate a detailed report after upload
  python upload_data.py data/*.csv --sqlite data.db --report
        """
    )
    
    # Required arguments
    parser.add_argument('csv_files', nargs='+', type=str,
                        help='Path(s) to CSV file(s) to upload. Can include directories or glob patterns.')
    
    # Output format selection (mutually exclusive)
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument('--cosmos', action='store_true',
                       help='Upload to Cosmos DB')
    output_group.add_argument('--sqlite', type=str, metavar='DB_PATH',
                       help='Upload to SQLite database at the specified path')
    output_group.add_argument('--json', action='store_true',
                       help='Save to JSON files')
    output_group.add_argument('--csv', action='store_true',
                       help='Save to CSV files (useful for transformations)')
    
    # Cosmos DB specific arguments
    cosmos_group = parser.add_argument_group('Cosmos DB options')
    cosmos_group.add_argument('--container', type=str, default=None,
                        help='Name of the Cosmos DB container (default: derived from filename)')
    cosmos_group.add_argument('--city', type=str, default=None,
                        help='City name to use as partition key if missing in records')
    
    # SQLite specific arguments
    sqlite_group = parser.add_argument_group('SQLite options')
    sqlite_group.add_argument('--table', type=str, default='ads',
                        help='Name of the SQLite table (default: ads)')
    
    # File output arguments
    file_group = parser.add_argument_group('File output options')
    file_group.add_argument('--output-dir', type=str, default='.',
                        help='Directory to save output files (default: current directory)')
    
    # Common arguments
    parser.add_argument('--batch-size', '-b', type=int, default=50,
                        help='Number of records to upload in a single batch (default: 50)')
    parser.add_argument('--report', '-r', action='store_true', default=False,
                        help='Generate a detailed JSON report after upload')
    parser.add_argument('--config', '-c', type=str, default=None,
                        help='Path to config file (default: use environment variables)')
    
    return parser.parse_args()

def main():
    """Main function to handle uploading CSV data."""
    args = parse_arguments()
    
    # Load configuration
    config = load_configuration(args.config)
    
    # Find all CSV files matching the patterns
    csv_paths = find_csv_files(args.csv_files)
    
    if not csv_paths:
        logger.error("No CSV files found matching the provided patterns")
        sys.exit(1)
    
    logger.info(f"Found {len(csv_paths)} CSV files to process")
    
    # Create a mock retriever (not used for direct retrieval)
    retriever = RealEstateAdRetriever.create_mock_retriever(config)
    
    # Initialize data manager
    data_manager = RealEstateDataManager(retriever, config)
    
    # Process each CSV file
    all_results = []
    success_count = 0
    
    for csv_path in csv_paths:
        logger.info(f"Processing file: {csv_path}")
        
        # Extract metadata from filename to help with defaults
        metadata = extract_metadata_from_filename(csv_path)
        
        # Determine output parameters based on the selected format
        output_params = {}
        output_format = None
        
        if args.cosmos:
            output_format = 'cosmos'
            # Determine container name
            container_name = args.container
            if not container_name:
                container_name = metadata.get('contract_type', 'ads')
                if metadata.get('city'):
                    container_name = f"{metadata['city']}_{container_name}"
            
            # Add city for partition key
            city = args.city or metadata.get('city')
            
            output_params = {
                'container_name': container_name,
                'city': city
            }
            
            logger.info(f"Uploading to Cosmos DB container: {container_name}")
            
        elif args.sqlite:
            output_format = 'sqlite'
            output_params = {
                'db_path': args.sqlite,
                'table_name': args.table
            }
            logger.info(f"Uploading to SQLite database: {args.sqlite}, table: {args.table}")
            
        elif args.json:
            output_format = 'json'
            filename = Path(args.output_dir) / f"{csv_path.stem}"
            output_params = {'filename': str(filename)}
            logger.info(f"Saving to JSON: {filename}.json")
            
        elif args.csv:
            output_format = 'csv'
            filename = Path(args.output_dir) / f"{csv_path.stem}_processed"
            output_params = {'filename': str(filename)}
            logger.info(f"Saving to CSV: {filename}.csv")
        
        # Upload the data using data_manager
        result = upload_csv_with_batches(
            csv_path=csv_path,
            data_manager=data_manager,
            output_format=output_format,
            batch_size=args.batch_size,
            **output_params
        )
        
        all_results.append(result)
        if result['successful'] > 0:
            success_count += 1
    
    # Print summary
    logger.info("\n[SUMMARY]")
    logger.info(f"Total files processed: {len(csv_paths)}")
    logger.info(f"Files with successful uploads: {success_count}")
    
    for result in all_results:
        logger.info(f"- {Path(result['file']).name}: {result['successful']}/{result['total_records']} records uploaded to {result['output_format']}")
    
    # Generate detailed report if requested
    if args.report:
        report_path = f"upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                # Convert datetime objects to strings for JSON serialization
                report_data = []
                for result in all_results:
                    result_copy = result.copy()
                    result_copy['start_time'] = result_copy['start_time'].isoformat()
                    result_copy['end_time'] = result_copy['end_time'].isoformat() if result_copy['end_time'] else None
                    report_data.append(result_copy)
                
                json.dump(report_data, f, indent=2)
                
            logger.info(f"Detailed report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")

if __name__ == "__main__":
    main()
