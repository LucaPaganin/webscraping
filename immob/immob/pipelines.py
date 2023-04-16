# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import json
from pathlib import Path
from itemadapter import ItemAdapter

IDS_FILE = Path("ids.json")

class JsonWriterPipeline:

    def open_spider(self, spider):
        self.file = open('items.jsonl', 'w')
        self.ids = set(json.loads(IDS_FILE.read_text()))

    def close_spider(self, spider):
        self.file.close()
        IDS_FILE.write_text(json.dumps(list(self.ids), indent=2))

    def process_item(self, item, spider):
        if item['id'] not in self.ids:
            line = json.dumps(ItemAdapter(item).asdict()) + "\n"
            self.file.write(line)
            self.ids.add(item['id'])
            return item
        else:
            raise DropItem(item)
