import scrapy
from scrapy.loader import ItemLoader
from immob.items import ImmobItem


class ImmobitSpider(scrapy.Spider):
    name = "immobit"
    allowed_domains = ["immobiliare.it"]
    
    def start_requests(self):
        self.sibling_mapping = {
            'data': "Riferimento e Data annuncio",
            'stato': "stato",
            "spese_condominio": "spese condominio",
            "numero_piani": "totale piani edificio"
        }
        start_urls = [
            "https://www.immobiliare.it/vendita-case/genova/con-piani-intermedi/?criterio=rilevanza&prezzoMassimo=240000&superficieMinima=60&superficieMassima=100&fasciaPiano[]=30&idMZona[]=10248&idMZona[]=10255&idMZona[]=10352&idMZona[]=10256&idMZona[]=10247&idMZona[]=10350&idQuartiere[]=10059&idQuartiere[]=11504&idQuartiere[]=10050&idQuartiere[]=10046&idQuartiere[]=13165"
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        announcements = response.xpath("//ul[@data-cy='result-list']//a[@class='in-card__title']")
        for announce in announcements:
            yield scrapy.Request(
                url=announce.attrib['href'], 
                callback=self.parse_announce_page, 
                meta={
                    'title': announce.attrib['title'], 
                    'url': announce.attrib['href']
                    }
                )

        nextpage = response.xpath("//div[@data-cy='pagination-next']//a[@class='in-pagination__item' and @role='link']")
        if nextpage:
            yield scrapy.Request(url=nextpage[0].attrib['href'], callback=self.parse)
        else:
            print("last page")
    
    def parse_announce_page(self, response):
        try:
            loader = ItemLoader(item=ImmobItem(), response=response)
            ul_xpath = "//ul[contains(@class, 'in-landingDetail__mainFeatures')]"
            loader.add_xpath('prezzo', "//li[contains(@class, 'in-detail__mainFeaturesPrice')]/text()")
            loader.add_xpath(
                'zona', 
                "//div[@class='in-titleBlock__content']//span[@class='in-location']/text()"
            )
            
            for key in ['locali', 'superficie', 'piano']:
                loader.add_xpath(key, f"{ul_xpath}//li[@aria-label='{key}']")
            loader.add_xpath('bagni', f"{ul_xpath}//li[starts-with(@aria-label, 'bagn')]")
            
            for key, sibling in self.sibling_mapping.items():
                loader.add_xpath(key, f"//dt[@class='in-realEstateFeatures__title' and text() = '{sibling}']/following-sibling::*")
            item = loader.load_item()
            item['title'] = response.meta['title']
            item['url'] = response.meta['url']
            item['id'] = item['url'].rstrip("/").split("/")[-1]
            item['citta'] = item['zona'][0]
            item['quartiere'] = item['zona'][1]
            try:
                item['via'] = item['zona'][2]
            except IndexError:
                item['via'] = ""
            # print(item)
            return item
        except BaseException as e:
            print(e)