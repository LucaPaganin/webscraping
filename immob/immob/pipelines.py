# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import json, pandas as pd
from pathlib import Path
from itemadapter import ItemAdapter
from common.gsheets import GSheetPipeline

IDS_FILE = Path("ids.json")

class ImmobPipeline(GSheetPipeline):
    def open_spider(self, spider):
        super().open_spider(spider)
        self.file = open('items.jsonl', 'w')

    def close_spider(self, spider):
        super().close_spider(spider)
        self.file.close()
        IDS_FILE.write_text(json.dumps(list(self.ids), indent=2))

    def process_item(self, item, spider):
        if item['id'] not in self.ids:
            itemdict = ItemAdapter(item).asdict()
            appendvalue = self._get_append_value(itemdict)
            self.file.write(json.dumps(itemdict) + "\n")
            self.appendvalues.append(appendvalue)
            self.ids.add(item['id'])
            return item
        else:
            raise DropItem(item)
