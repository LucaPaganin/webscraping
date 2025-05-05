#!/usr/bin/env python
"""
Helper script to run the Selenium-based spider with convenient arguments.
Run this script directly to launch the Selenium spider.
"""

import os
import sys
from scrapy.cmdline import execute

# Ensure proper path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Arguments for the spider
try:
    url = sys.argv[1] if len(sys.argv) > 1 else None
    
    args = ['scrapy', 'crawl', 'immobit_selenium']
    
    # Add debug level
    args.extend(['-L', 'DEBUG'])
    
    # Add start URL if provided
    if url:
        args.extend(['-a', f'start_url={url}'])
    
    # Execute the spider with the arguments
    execute(args)
    
except Exception as e:
    print(f"Error running spider: {e}")
    print("\nUsage:")
    print("python run_selenium_spider.py [URL]")
    print("\nExample:")
    print("python run_selenium_spider.py https://www.immobiliare.it/annunci/120065826/")
    sys.exit(1)
