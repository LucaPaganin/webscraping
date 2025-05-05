# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import json, pandas as pd
from pathlib import Path
import logging
import datetime
from scrapy.utils.project import get_project_settings

# Legacy constants for backwards compatibility
IDS_FILE = Path("ids.json")
OUTPUT_DIR = Path("output")

class GenericJSONPipeline:
    """
    Generic pipeline to store data in structured JSON files
    with each spider's data stored in its own directory.
    
    Settings:
    - JSON_OUTPUT_DIR: Base directory for JSON output (default: "output")
    - JSON_KEEP_IDS: Whether to track and save processed IDs (default: True)
    - JSON_DEDUPLICATE: Whether to drop duplicate items (default: True)
    - JSON_ID_FIELD: The field to use as the unique ID (default: "id")
    - JSON_INDENT: JSON indentation level (default: 2)
    """
    
    def __init__(self):
        settings = get_project_settings()
        self.base_output_dir = Path(settings.get('JSON_OUTPUT_DIR', 'output'))
        self.keep_ids = settings.get('JSON_KEEP_IDS', True)
        self.deduplicate = settings.get('JSON_DEDUPLICATE', True)
        self.id_field = settings.get('JSON_ID_FIELD', 'id')
        self.indent = settings.get('JSON_INDENT', 2)
        
        # These will be set per-spider in the open_spider method
        self.items = []
        self.ids = set()
        self.spider_output_dir = None
        self.json_file = None
        self.ids_file = None
    
    def open_spider(self, spider):
        """Called when a spider starts - set up directories and files for this spider"""
        # Create spider-specific output directory
        self.spider_output_dir = self.base_output_dir / spider.name
        self.spider_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up timestamp and filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.json_file = self.spider_output_dir / f"{spider.name}_data_{timestamp}.json"
        self.ids_file = self.spider_output_dir / f"{spider.name}_ids.json"
        
        # Load existing IDs if we're keeping track
        if self.keep_ids and self.deduplicate and self.ids_file.exists():
            try:
                self.ids = set(json.loads(self.ids_file.read_text()))
                logging.info(f"Loaded {len(self.ids)} existing IDs for spider '{spider.name}'")
            except json.JSONDecodeError:
                logging.warning(f"Could not parse {self.ids_file}, starting with empty ID set")
        
        logging.info(f"GenericJSONPipeline initialized for spider '{spider.name}'. Output: {self.json_file}")
    
    def close_spider(self, spider):
        """Called when the spider closes - save all items to a JSON file"""
        # Save all items to a structured JSON file
        with open(self.json_file, 'w', encoding='utf-8') as f:
            output_data = {
                "metadata": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "spider": spider.name,
                    "count": len(self.items)
                },
                "items": self.items
            }
            
            # Add custom metadata if the spider provides it
            if hasattr(spider, 'get_metadata'):
                output_data["metadata"].update(spider.get_metadata())
                
            json.dump(output_data, f, ensure_ascii=False, indent=self.indent)
        
        # Save IDs for future deduplication if configured
        if self.keep_ids:
            self.ids_file.write_text(json.dumps(list(self.ids), indent=self.indent))
            logging.info(f"Saved {len(self.ids)} IDs to {self.ids_file}")
        
        logging.info(f"Saved {len(self.items)} items to {self.json_file}")
    
    def process_item(self, item, spider):
        """Process each item, checking for duplicates and adding to the list"""
        # Check if this item has an ID we can use for deduplication
        item_id = item.get(self.id_field)
        
        if self.deduplicate:
            if not item_id:
                logging.warning(f"Item without '{self.id_field}' found in spider '{spider.name}'")
                # Still process the item even without an ID
            elif item_id in self.ids:
                raise DropItem(f"Duplicate item found: {item_id}")
        
        # Convert item to dict and store
        item_dict = ItemAdapter(item).asdict()
        self.items.append(item_dict)
        
        # If we have an ID, add it to our set
        if item_id and self.deduplicate:
            self.ids.add(item_id)
        
        return item  # Return item for other pipelines


