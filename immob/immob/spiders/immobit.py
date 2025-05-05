import scrapy
from scrapy.loader import ItemLoader
from immob.items import ImmobItem, ImmobAnnounceItem


class ImmobitSpider(scrapy.Spider):
    name = "immobit"
    allowed_domains = ["immobiliare.it"]
    
    # Puoi mantenere il sibling_mapping se ti serve nella parse_announce_page,
    # ma non è usato in questa versione aggiornata della parse.
    # self.sibling_mapping = { ... }

    def start_requests(self):
        self.sibling_mapping = {
            'data': "Riferimento e Data annuncio",
            'stato': "stato",
            "spese_condominio": "spese condominio",
            "numero_piani": "totale piani edificio",
            "posti_auto": "Posti Auto"
        }
        # Mantieni la logica per le richieste iniziali come l'avevi definita
        start_urls = [
            "https://www.immobiliare.it/affitto-case/savona/"
        ]
        for url in start_urls:
            # Usa un user-agent realistico come discusso
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
            )

    def parse(self, response):
        # Questo metodo processa la pagina della lista annunci
        # Trova tutti i blocchi che rappresentano un singolo annuncio nella lista
        # Usiamo il selettore CSS che hai identificato
        announcement_items = response.css("li.nd-list__item.in-searchLayoutListItem")

        # Itera su ogni singolo elemento LI (ogni annuncio nella lista)
        for item in announcement_items:
            # 'item' è un selettore Scrapy che punta a un singolo blocco annuncio <li>.
            # Usiamo .css() o .xpath() su questo 'item' per selezionare elementi *relativi a esso*.

            # --- Estrazione dei dati di ANTEPRIMA dalla LISTA ---

            # Estrai il titolo dell'annuncio dal link
            # Seleziona l'elemento <a> del titolo dentro l'item e prendi l'attributo 'title'
            title = item.css('a.in-listingCardTitle::attr(title)').get()

            # Estrai il prezzo visibile nella lista
            # Seleziona lo <span> del prezzo dentro l'item e prendi il testo
            prezzo_anteprima = item.css('.in-listingCardPrice span::text').get()

            # Estrai l'URL del link alla pagina di dettaglio
            # Seleziona l'elemento <a> che contiene il link e prendi l'attributo 'href'
            # Nota: il selettore '.in-listingCardProperty a' potrebbe essere più specifico se necessario
            url_dettaglio_relative = item.css('a.in-listingCardTitle::attr(href)').get()
            # Alternativa se il link è in un <a> diverso:
            # url_dettaglio_relative = item.css('.in-listingCardProperty a::attr(href)').get()


            # Estrai l'URL dell'immagine di anteprima
            # Seleziona l'elemento <img> dentro l'item e prendi l'attributo 'src'
            immagine_anteprima = item.css('img::attr(src)').get()
            # Potrebbe esserci più di un'immagine, questo prende la prima.

            # Estrai le caratteristiche brevi visibili nella lista (es. locali, bagni, mq)
            # Seleziona tutti gli <span> con la classe 'in-listingCardFeatureList__item'
            # che sono discendenti dell'item corrente e prendi il testo
            # Usiamo .getall() per ottenere una lista di tutti i testi trovati
            caratteristiche_anteprima = item.css('.in-listingCardFeatureList__item span::text').getall()

            # --- Fine Estrazione Anteprima ---

            # --- Mapping caratteristiche_anteprima ---
            def map_caratteristiche(caratteristiche):
                mapping = {
                    'locali': None,
                    'superficie': None,
                    'bagni': None,
                    'piano': None,
                    'ascensore': None,
                    'balcone': None,
                    'arredato': None,
                    'cantina': None,
                    'terrazzo': None,
                }
                for c in caratteristiche:
                    c_lower = c.lower()
                    if 'locale' in c_lower:
                        mapping['locali'] = c
                    elif 'm²' in c_lower or 'mq' in c_lower:
                        mapping['superficie'] = c
                    elif 'bagno' in c_lower:
                        mapping['bagni'] = c
                    elif 'piano' in c_lower:
                        mapping['piano'] = c
                    elif 'ascensore' in c_lower:
                        mapping['ascensore'] = c
                    elif 'balcone' in c_lower:
                        mapping['balcone'] = c
                    elif 'arredato' in c_lower:
                        mapping['arredato'] = c
                    elif 'cantina' in c_lower:
                        mapping['cantina'] = c
                    elif 'terrazzo' in c_lower:
                        mapping['terrazzo'] = c
                return mapping

            caratteristiche_mapped = map_caratteristiche(caratteristiche_anteprima)
            
            full_url = response.urljoin(url_dettaglio_relative) if url_dettaglio_relative else None

            # --- Yield ImmobAnnounceItem for preview ---
            announce_item = ImmobAnnounceItem()
            announce_item['title'] = title
            announce_item['url'] = full_url
            announce_item['id'] = announce_item['url'].rstrip("/").split("/")[-1] if announce_item['url'] else None
            announce_item['prezzo_lista_preview'] = prezzo_anteprima
            announce_item['caratteristiche_lista_preview'] = caratteristiche_anteprima
            announce_item['immagine_lista_preview'] = immagine_anteprima
            for k, v in caratteristiche_mapped.items():
                announce_item[k] = v
            

            # Costruisci l'URL completo per la pagina di dettaglio
            

            # Verifica se abbiamo trovato un URL di dettaglio valido prima di procedere
            if full_url:
                # Yield la Request per la pagina di dettaglio
                # Passiamo le info di anteprima nella meta se ci serviranno nella parse_announce_page
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_announce_page,
                    meta={
                        'title': title,
                        'url': full_url, # L'URL completo
                        'prezzo_lista_preview': prezzo_anteprima,
                        'caratteristiche_lista_preview': caratteristiche_anteprima,
                        'immagine_lista_preview': immagine_anteprima
                        # Puoi aggiungere qui altre info estratte dalla lista se necessario
                    }
                )
            else:
                 # Logga un avviso se non siamo riusciti a trovare il link di dettaglio per un item
                 self.logger.warning(f"Link dettaglio non trovato per un item sulla pagina: {response.url}")


        # --- Logica per passare alla pagina successiva ---
        # Seleziona il link alla pagina successiva DALLA RESPONSE COMPLETA, non dall'item
        # Usiamo .get() direttamente sull'XPath per prendere l'attributo href del primo elemento trovato
        next_page_relative_url = response.xpath("//div[@data-cy='pagination-next']//a[@class='in-pagination__item' and @role='link']/@href").get()

        if next_page_relative_url:
            # Costruisci l'URL completo della pagina successiva
            next_page_url = response.urljoin(next_page_relative_url)
            self.logger.info(f"Found next page: {next_page_url}")
            # Yield una nuova Request per la pagina successiva, chiamando di nuovo il metodo parse
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                 headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'} # Mantieni lo user agent
            )
        else:
            self.logger.info(f"Last page reached: {response.url}")
    
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