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
            # User-Agent is now handled by RandomUserAgentMiddleware
            yield scrapy.Request(
                url=url,
                callback=self.parse
            )

    # Function to map caratteristiche_anteprima to specific fields
    def map_caratteristiche(self, caratteristiche):
        """
        Maps caratteristiche_anteprima array items to their respective fields
        Returns a dictionary with field names as keys and their values
        """
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
            c_lower = c.lower() if c else ""
            if not c_lower:
                continue
                
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

    def parse(self, response):
        # Questo metodo processa la pagina della lista annunci
        # Trova tutti i blocchi che rappresentano un singolo annuncio nella lista
        # Usiamo il selettore CSS che hai identificato
        announcement_items = response.css("li.nd-list__item.in-searchLayoutListItem")

        # Itera su ogni singolo elemento LI (ogni annuncio nella lista)
        for item_selector in announcement_items:
            loader = ItemLoader(item=ImmobAnnounceItem(), selector=item_selector)
            loader.add_css('title', 'a.in-listingCardTitle::attr(title)')
            loader.add_css('prezzo_lista_preview', '.in-listingCardPrice span::text')
            loader.add_css('prezzo', '.in-listingCardPrice span::text')
            loader.add_css('url', 'a.in-listingCardTitle::attr(href)')
            loader.add_css('immagine_lista_preview', 'img::attr(src)')
            loader.add_css('caratteristiche_lista_preview', '.in-listingCardFeatureList__item span::text')

            # Get caratteristiche_anteprima to map them to specific fields
            caratteristiche_lista_raw = item_selector.css('.in-listingCardFeatureList__item span::text').getall()
            caratteristiche_mapped = self.map_caratteristiche(caratteristiche_lista_raw)
            
            # Add each mapped field to the loader
            for field, value in caratteristiche_mapped.items():
                if value is not None:
                    loader.add_value(field, value)
            
            # Load all fields
            announce_item = loader.load_item()

            # Fix url to be absolute and set ID
            if 'url' in announce_item and announce_item['url']:
                full_url = response.urljoin(announce_item['url'])
                announce_item['url'] = full_url
                announce_item['id'] = full_url.rstrip("/").split("/")[-1]
            else:
                full_url = None
                announce_item['id'] = None

            # Don't yield the announce_item from the list page yet
            # Instead, first get the details and then yield a complete item
            
            # Verifica se abbiamo trovato un URL di dettaglio valido prima di procedere
            if full_url:
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_announce_page,
                    meta={
                        'item': announce_item  # Pass the entire item
                    }
                )
            else:
                # If we couldn't get a detail URL, yield the basic item
                self.logger.warning(f"Link dettaglio non trovato per un item sulla pagina: {response.url}")
                yield announce_item


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
                callback=self.parse
            )
        else:
            self.logger.info(f"Last page reached: {response.url}")
    
    def parse_announce_page(self, response):
        try:
            # Get the item from the list page
            announce_item = response.meta['item']
            
            # Create a new loader with the ImmobAnnounceItem we already have
            # This allows us to enrich the same item type rather than creating a new one
            loader = ItemLoader(item=announce_item, response=response)
            
            # Extract detailed information from the announce page
            ul_xpath = "//ul[contains(@class, 'in-landingDetail__mainFeatures')]"
            
            # Only add these fields if they might have better data on the detail page
            loader.add_xpath('prezzo', "//li[contains(@class, 'in-detail__mainFeaturesPrice')]/text()")
            
            # Add fields that are only available on the detail page
            loader.add_xpath(
                'zona', 
                "//div[@class='in-titleBlock__content']//span[@class='in-location']/text()"
            )
            
            # These might have better data on the detail page
            for key in ['locali', 'superficie', 'piano']:
                loader.add_xpath(key, f"{ul_xpath}//li[@aria-label='{key}']")
            loader.add_xpath('bagni', f"{ul_xpath}//li[starts-with(@aria-label, 'bagn')]")
            
            # Add additional fields from the detail page
            for key, sibling in self.sibling_mapping.items():
                loader.add_xpath(key, f"//dt[@class='in-realEstateFeatures__title' and text() = '{sibling}']/following-sibling::*")
            
            # Load the enriched item
            item = loader.load_item()
            
            # Process zona field if it exists to extract city, neighborhood, etc.
            if 'zona' in item:
                parts = item['zona']
                if isinstance(parts, list) and len(parts) > 0:
                    item['citta'] = parts[0]
                    if len(parts) > 1:
                        item['quartiere'] = parts[1]
                    if len(parts) > 2:
                        item['via'] = parts[2]
            
            # Yield the enriched item to the pipeline
            yield item
            
        except Exception as e:
            self.logger.error(f"Error parsing announce page: {e}")
            # In case of error, try to yield the original item if available
            if 'item' in response.meta:
                self.logger.info(f"Yielding list page item as fallback for {response.url}")
                yield response.meta['item']