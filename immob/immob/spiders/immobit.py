import scrapy


class ImmobitSpider(scrapy.Spider):
    name = "immobit"
    allowed_domains = ["immobiliare.it"]
    
    def start_requests(self):
        self.file = open("test.txt", "w")
        self.count = 0
        start_urls = [
            "https://www.immobiliare.it/vendita-case/genova/con-piani-intermedi/?prezzoMinimo=80000&prezzoMassimo=220000&superficieMinima=60&superficieMassima=80&localiMinimo=2&fasciaPiano%5B0%5D=30&idMZona%5B0%5D=10248&idQuartiere%5B0%5D=10059&idQuartiere%5B1%5D=11504&id=101835256"
        ]
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        announcements = response.xpath("//ul[@data-cy='result-list']//a[@class='in-card__title']")
        for announce in announcements:
            yield scrapy.Request(url=announce.attrib['href'], 
                                 callback=self.parse_announce_page, 
                                 meta={'title': announce.attrib['title']})
        
        
        nextpage = response.xpath("//div[@data-cy='pagination-next']").xpath("//a[@class='in-pagination__item' and @role='link']")
        if nextpage:
            yield scrapy.Request(url=nextpage.attrib['href'], 
                                 callback=self.parse)
        else:
            print("last page")
            self.file.close()
    
    def parse_announce_page(self, response, *args, **kwargs):
        self.count += 1
        print(response)
        print(self.count)
        self.file.write(f"{self.count}: {response.meta['title']}\n")