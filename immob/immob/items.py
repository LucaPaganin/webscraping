# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
import re, traceback
import scrapy

def TE(func):
    def inner(x):
        try:
            return func(x)
        except:
            print(traceback.format_exc())
            return x
    return inner

def parse_price(price):
    newprice = remove_tags(price).split()[-1]
    return re.sub(r"(\.|,\d+)", "", newprice)

def parse_surface(surface):
    return remove_tags(surface).split("m")[0]

def parse_floor(floor):
    return remove_tags(floor).replace("T", "0")

def parse_date(date):
    date = remove_tags(date)
    match = re.search(r"\d{1,2}/\d{1,2}/\d{1,4}", date)
    if match:
        return date[match.start():match.end()]
    else:
        return date

def parse_digits(numfloors):
    numfloors = remove_tags(str(numfloors))
    match = re.search(r"(\d+)", numfloors)
    if match:
        return match.groups()[0]
    else:
        return numfloors

def apply_takefirst(func, defval=None):
    def inner(x):
        val = TakeFirst()(x)
        if val is None:
            val = defval
        return func(val)
    return inner

class ImmobItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    zona = scrapy.Field()
    citta = scrapy.Field()
    quartiere = scrapy.Field()
    via = scrapy.Field()
    prezzo = scrapy.Field(
        input_processor=MapCompose(parse_price),
        output_processor=Join()
    )
    superficie = scrapy.Field(
        input_processor=MapCompose(parse_surface),
        output_processor=Join()
    )
    locali = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=Join()
    )
    piano = scrapy.Field(
        input_processor=MapCompose(parse_floor),
        output_processor=Join()
    )
    bagni = scrapy.Field(
        input_processor=apply_takefirst(remove_tags, defval=""),
        output_processor=Join()
    )
    numero_piani = scrapy.Field(
        input_processor=apply_takefirst(parse_digits),
        output_processor=Join()
    )
    posti_auto = scrapy.Field(
        input_processor=apply_takefirst(remove_tags, defval=""),
        output_processor=Join()
    )
    data = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_date)
    )
    stato = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(remove_tags)
    )
    spese_condominio = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_digits)
    )
     

