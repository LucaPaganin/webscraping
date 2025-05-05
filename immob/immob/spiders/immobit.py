import scrapy
from scrapy.loader import ItemLoader
from immob.items import ImmobItem, ImmobAnnounceItem


class ImmobitSpider(scrapy.Spider):
    name = "immobit"
    allowed_domains = ["immobiliare.it"]
    
    # Custom headers to make requests appear more like a real browser
    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Sec-CH-UA': '"Microsoft Edge";v="125", "Not:A-Brand";v="99", "Chromium";v="125"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        }
    }
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(ImmobitSpider, self).__init__(*args, **kwargs)
        self.start_url = start_url
        self.logger.info(f"Spider initialized with start_url: {start_url}" if start_url else "Spider initialized with default URLs")
    
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
        
        # Single URL mode for debugging
        if hasattr(self, 'start_url') and self.start_url:
            self.logger.info(f"Starting in single URL mode: {self.start_url}")
            
            # For single URL mode, we directly parse the detail page
            yield scrapy.Request(
                url=self.start_url,
                callback=self.parse_announce_page,
                dont_filter=True,
                meta={
                    'cookiejar': 1,
                    'handle_httpstatus_list': [403, 302, 503],
                    'dont_merge_cookies': False,
                    # Create a dummy item with id and url for single URL mode
                    'item': {'id': self.start_url.rstrip("/").split("/")[-1], 'url': self.start_url}
                }
            )
            return
            
        # Normal mode - first visit the homepage to establish a session
        yield scrapy.Request(
            url="https://www.immobiliare.it/",
            callback=self._after_homepage,
            dont_filter=True,
            meta={
                'cookiejar': 1,  # Use a cookiejar to maintain the session
                'handle_httpstatus_list': [403, 302, 503],  # Handle these status codes
                'dont_merge_cookies': False  # Allow cookie passing
            }
        )
        
    def _after_homepage(self, response):
        """
        After visiting the homepage to establish cookies/session,
        proceed with the actual search pages
        """
        if response.status != 200:
            self.logger.error(f"Failed to access homepage: status {response.status}")
            return
            
        self.logger.info(f"Successfully accessed homepage, proceeding with searches")
        
        # Real estate search URLs
        start_urls = [
            "https://www.immobiliare.it/affitto-case/savona/"
        ]
        
        for url in start_urls:
            # Use the established session
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'cookiejar': 1,  # Use the same cookiejar as before
                    'dont_merge_cookies': False,
                    'handle_httpstatus_list': [403, 302, 503]
                },
                headers={
                    # Add a referrer to simulate coming from the main site
                    'Referer': 'https://www.immobiliare.it/'
                }
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
        # Check if we got a successful response
        if response.status != 200:
            self.logger.error(f"Failed to access listings page: {response.url}, status: {response.status}")
            return
            
        # Log successful access
        self.logger.info(f"Successfully accessed listings page: {response.url}")
            
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
                # Add a small delay between requests by setting a priority
                import random
                
                # Pass cookies and session information from the list page request
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_announce_page,
                    meta={
                        'item': announce_item,  # Pass the entire item
                        'cookiejar': response.meta.get('cookiejar', 1),  # Use same session
                        'dont_merge_cookies': False,
                        'download_delay': random.uniform(3.0, 6.0),  # Individual delay for this request
                        'handle_httpstatus_list': [403, 302, 503],
                        'max_retry_times': 5  # Allow more retries for detail pages
                    },
                    headers={
                        # Use the current page as referer to appear more natural
                        'Referer': response.url
                    },
                    priority=random.randint(-10, 10)  # Randomize request order a bit
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
            
            # Randomize delay for pagination to avoid detection
            import random
            delay = random.uniform(5.0, 8.0)
            self.logger.info(f"Waiting {delay:.1f}s before processing next page")
            
            # Yield una nuova Request per la pagina successiva, chiamando di nuovo il metodo parse
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                meta={
                    # Pass session cookies forward
                    'cookiejar': response.meta.get('cookiejar', 1),
                    'dont_merge_cookies': False,
                    'download_delay': delay,
                    'handle_httpstatus_list': [403, 302, 503],
                },
                headers={
                    'Referer': response.url  # Use current page as referrer
                }
            )
        else:
            self.logger.info(f"Last page reached: {response.url}")
    
    def parse_announce_page(self, response):
        """
        Parse the detail page of a property announcement.
        Extracts 37 detailed fields including property characteristics,
        pricing information, location details, energy efficiency, etc.
        """
        # Check if we got a successful response
        if response.status != 200:
            self.logger.error(f"Failed to fetch detail page: {response.url}, status: {response.status}")
            self.logger.debug(f"Response headers: {response.headers}")
            
            # Enhanced error logging to help diagnose the 403 issue
            try:
                # Check if there's a CAPTCHA or anti-bot message in the response
                body_text = response.body.decode('utf-8', errors='replace')
                
                # Check for common anti-bot indicators
                indicators = [
                    "captcha", "robot", "automated", "blocked", "denied", 
                    "access forbidden", "suspicious", "unusual activity"
                ]
                
                found_indicators = [ind for ind in indicators if ind.lower() in body_text.lower()]
                if found_indicators:
                    self.logger.warning(f"Anti-bot indicators found: {found_indicators}")
                
                # Save response body for inspection
                import os
                import time
                debug_dir = os.path.join(self.settings.get('JSON_OUTPUT_DIR', 'output'), 'debug')
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                
                filename = os.path.join(debug_dir, f"detail_error_{int(time.time())}.html")
                with open(filename, 'wb') as f:
                    f.write(response.body)
                self.logger.info(f"Response body saved to {filename}")
                
            except Exception as e:
                self.logger.error(f"Error analyzing response: {e}")
            
            # Yield the basic item as fallback
            if 'item' in response.meta:
                self.logger.info(f"Yielding list page item as fallback for {response.url}")
                yield response.meta['item']
            return
            
        # Log successful access of detail page
        self.logger.info(f"Successfully accessed detail page: {response.url}")
        
        try:
            # Get the item from the list page or create a new one for single URL mode
            if 'item' in response.meta and isinstance(response.meta['item'], dict):
                # Convert dict to ImmobAnnounceItem if needed (for single URL mode)
                if not isinstance(response.meta['item'], scrapy.Item):
                    from immob.items import ImmobAnnounceItem
                    announce_item = ImmobAnnounceItem()
                    announce_item['id'] = response.meta['item'].get('id')
                    announce_item['url'] = response.url
                else:
                    announce_item = response.meta['item']
            else:
                # Create a new item if none exists
                from immob.items import ImmobAnnounceItem
                announce_item = ImmobAnnounceItem()
                announce_item['id'] = response.url.rstrip("/").split("/")[-1]
                announce_item['url'] = response.url
            
            # Create a loader with the item we already have from the list page
            loader = ItemLoader(item=announce_item, response=response)
            
            # Define the common XPath pattern for properties
            prop_xpath = "//div[contains(@class, 'im-properties__title') and contains(text(), '{0}')]/following-sibling::div/text()"
            features_xpath = "//ul[contains(@class, 'in-landingDetail__mainFeatures')]"
            
            # --- IDENTIFICATION AND META INFORMATION ---
            loader.add_xpath('riferimento_annuncio', prop_xpath.format('Riferimento Annuncio'))
            loader.add_xpath('data_pubblicazione', prop_xpath.format('Data Pubblicazione Annuncio'))
            loader.add_xpath('data_aggiornamento', prop_xpath.format('Data Aggiornamento Annuncio'))
            loader.add_xpath('codice_immobiliare', prop_xpath.format('Codice Immobiliare'))
            
            # --- DESCRIPTION ---
            # Get the complete description text, multiple paragraphs
            loader.add_xpath('descrizione', "//div[contains(@class, 'im-description__text')]//text()")
            
            # --- LOCATION INFORMATION ---
            loader.add_xpath('citta', prop_xpath.format('Città'))
            loader.add_xpath('provincia', prop_xpath.format('Provincia'))
            loader.add_xpath('regione', prop_xpath.format('Regione'))
            loader.add_xpath('zona', prop_xpath.format('Zona'))
            loader.add_xpath('indirizzo', prop_xpath.format('Indirizzo'))
            loader.add_xpath('cap', prop_xpath.format('CAP'))
            loader.add_xpath('quartiere', prop_xpath.format('Quartiere'))
            loader.add_xpath('distanza_dal_mare', prop_xpath.format('Distanza dal Mare'))
            
            # --- PROPERTY TYPE AND CONTRACT ---
            loader.add_xpath('tipologia', prop_xpath.format('Tipologia'))
            loader.add_xpath('categoria', prop_xpath.format('Categoria'))
            loader.add_xpath('contratto', prop_xpath.format('Contratto'))
            loader.add_xpath('tipo_contratto', prop_xpath.format('Tipo Contratto'))
            loader.add_xpath('tipo_proprieta', prop_xpath.format('Tipo Proprietà'))
            
            # --- MAIN PROPERTY CHARACTERISTICS ---
            # Try different selectors for primary features (main card vs. detailed sections)
            # Some fields might be in both places, the item loader's output processor will handle duplicates
            
            # Primary features from the main card
            loader.add_xpath('piano', f"{features_xpath}//li[@aria-label='piano']/text()")
            loader.add_xpath('superficie', f"{features_xpath}//li[@aria-label='superficie']/text()")
            loader.add_xpath('locali', f"{features_xpath}//li[@aria-label='locali']/text()")
            loader.add_xpath('bagni', f"{features_xpath}//li[starts-with(@aria-label, 'bagn')]/text()")
            
            # Try also in the detailed property section
            loader.add_xpath('piano', prop_xpath.format('Piano'))
            loader.add_xpath('piani_edificio', prop_xpath.format('Piani edificio')) 
            loader.add_xpath('totale_piani_edificio', prop_xpath.format('Totale piani edificio'))
            loader.add_xpath('ascensore', prop_xpath.format('Ascensore'))
            loader.add_xpath('superficie', prop_xpath.format('Superficie'))
            loader.add_xpath('locali', prop_xpath.format('Locali'))
            loader.add_xpath('bagni', prop_xpath.format('Bagni'))
            loader.add_xpath('camere_da_letto', prop_xpath.format('Camere da letto'))
            loader.add_xpath('camere', prop_xpath.format('Camere'))  # Alternative field
            loader.add_xpath('altre_stanze', prop_xpath.format('Altre stanze'))
            
            # --- PROPERTY FEATURES ---
            loader.add_xpath('arredato', prop_xpath.format('Arredato'))
            loader.add_xpath('cucina', prop_xpath.format('Cucina'))
            loader.add_xpath('balcone', prop_xpath.format('Balcone'))
            loader.add_xpath('terrazzo', prop_xpath.format('Terrazzo'))
            loader.add_xpath('giardino', prop_xpath.format('Giardino'))
            loader.add_xpath('cantina', prop_xpath.format('Cantina'))
            loader.add_xpath('soffitta', prop_xpath.format('Soffitta'))
            loader.add_xpath('taverna', prop_xpath.format('Taverna'))
            loader.add_xpath('mansarda', prop_xpath.format('Mansarda'))
            loader.add_xpath('posti_auto', prop_xpath.format('Posti Auto'))
            loader.add_xpath('box_auto', prop_xpath.format('Box Auto'))
            loader.add_xpath('anno_costruzione', prop_xpath.format('Anno di costruzione'))
            loader.add_xpath('stato', prop_xpath.format('Stato'))
            loader.add_xpath('stato_immobile', prop_xpath.format('Stato Immobile'))  # Alternative field
            
            # --- COMFORT AND AMENITIES ---
            loader.add_xpath('riscaldamento', prop_xpath.format('Riscaldamento')) 
            loader.add_xpath('tipo_riscaldamento', prop_xpath.format('Tipo riscaldamento'))
            loader.add_xpath('climatizzazione', prop_xpath.format('Climatizzazione'))
            loader.add_xpath('vista', prop_xpath.format('Vista'))
            loader.add_xpath('esposizione', prop_xpath.format('Esposizione'))
            loader.add_xpath('orientamento', prop_xpath.format('Orientamento'))
            
            # --- OTHER FEATURES ---
            # Get all additional features as a list
            loader.add_xpath('altre_caratteristiche', "//div[contains(@class, 'im-features__list')]//li/text()")
            
            # --- SURFACE DETAILS ---
            loader.add_xpath('dettaglio_superficie', prop_xpath.format('Superficie'))
            loader.add_xpath('coefficiente', prop_xpath.format('Coefficiente'))
            loader.add_xpath('tipo_superficie', prop_xpath.format('Tipo superficie'))
            loader.add_xpath('superficie_commerciale', prop_xpath.format('Superficie commerciale'))
            loader.add_xpath('superficie_coperta', prop_xpath.format('Superficie coperta'))
            loader.add_xpath('superficie_giardino', prop_xpath.format('Superficie giardino'))
            loader.add_xpath('superficie_terrazzo', prop_xpath.format('Superficie terrazzo'))
            loader.add_xpath('superficie_balcone', prop_xpath.format('Superficie balcone'))
            
            # --- ECONOMIC INFORMATION ---
            # Try the main price display first, then the detailed one
            loader.add_xpath('prezzo', "//li[contains(@class, 'in-detail__mainFeaturesPrice')]/text()")
            loader.add_xpath('prezzo', prop_xpath.format('Prezzo'))
            loader.add_xpath('prezzo_al_mq', prop_xpath.format('Prezzo al m²'))
            loader.add_xpath('spese_condominio', prop_xpath.format('Spese condominio'))
            loader.add_xpath('spese_extra', prop_xpath.format('Spese extra'))
            loader.add_xpath('cauzione', prop_xpath.format('Cauzione'))
            loader.add_xpath('caparra', prop_xpath.format('Caparra'))  # Alternative field
            
            # --- RENTAL SPECIFIC INFORMATION ---
            loader.add_xpath('durata_contratto', prop_xpath.format('Durata contratto'))
            loader.add_xpath('disponibilita', prop_xpath.format('Disponibilità'))
            loader.add_xpath('requisiti', prop_xpath.format('Requisiti'))
            loader.add_xpath('ideale_per', prop_xpath.format('Ideale per'))
            
            # --- ENERGY EFFICIENCY ---
            loader.add_xpath('classe_energetica', prop_xpath.format('Classe Energetica'))
            loader.add_xpath('indice_prestazione_energetica', prop_xpath.format('Indice di prestazione energetica'))
            loader.add_xpath('consumo_energetico', prop_xpath.format('Consumo di energia'))
            loader.add_xpath('ep_globale_non_rinnovabile', prop_xpath.format('EP globale non rinnovabile'))
            loader.add_xpath('prestazione_inverno', prop_xpath.format('Prestazione inverno'))
            loader.add_xpath('prestazione_estate', prop_xpath.format('Prestazione estate'))
            
            # --- BUILDING INFORMATION ---
            loader.add_xpath('portineria', prop_xpath.format('Portineria'))
            loader.add_xpath('tipo_edificio', prop_xpath.format('Tipo Edificio'))
            loader.add_xpath('num_unita', prop_xpath.format('Numero unità'))
            
            # --- AGENT INFORMATION ---
            loader.add_xpath('agente', prop_xpath.format('Agente'))
            loader.add_xpath('agenzia', prop_xpath.format('Agenzia'))
            
            # --- MEDIA ---
            # Get image URLs 
            loader.add_xpath('immagini', "//div[contains(@class, 'im-carousel')]//img/@src")
            
            # --- GEOGRAPHIC COORDINATES ---
            # Extract coordinates from map if present
            loader.add_xpath('latitudine', "//div[contains(@data-cy, 'map')]/@data-lat")
            loader.add_xpath('longitudine', "//div[contains(@data-cy, 'map')]/@data-lng")
            
            # Load the enriched item with all collected data
            item = loader.load_item()
            
            # --- POST-PROCESSING FOR DATA CLEANUP ---
            # Process boolean fields from strings like "Sì"/"No"/"Presente" to True/False
            bool_fields = [
                'ascensore', 'arredato', 'balcone', 'terrazzo', 'giardino', 
                'cantina', 'soffitta', 'mansarda', 'portineria', 'taverna'
            ]
            for field in bool_fields:
                if field in item and isinstance(item[field], str):
                    value = item[field].lower()
                    item[field] = ('sì' in value or 'si ' in value or 'presente' in value or 'yes' in value or 
                                  value == 'si' or value == 'true')
            
            # Process numeric fields with units and convert to appropriate types
            numeric_fields = {
                'superficie': r'(\d+(?:[\.,]\d+)?)\s*m²?',
                'superficie_commerciale': r'(\d+(?:[\.,]\d+)?)\s*m²?',
                'superficie_coperta': r'(\d+(?:[\.,]\d+)?)\s*m²?',
                'superficie_giardino': r'(\d+(?:[\.,]\d+)?)\s*m²?',
                'superficie_terrazzo': r'(\d+(?:[\.,]\d+)?)\s*m²?',
                'superficie_balcone': r'(\d+(?:[\.,]\d+)?)\s*m²?',
                'prezzo': r'€?\s*(\d+(?:[\.,]\d+)?)',
                'prezzo_al_mq': r'(\d+(?:[\.,]\d+)?)\s*€/m²',
                'spese_condominio': r'€?\s*(\d+(?:[\.,]\d+)?)',
                'spese_extra': r'€?\s*(\d+(?:[\.,]\d+)?)',
                'cauzione': r'€?\s*(\d+(?:[\.,]\d+)?)',
                'caparra': r'€?\s*(\d+(?:[\.,]\d+)?)',
                'consumo_energetico': r'(\d+(?:[\.,]\d+)?)\s*kWh/m²',
                'ep_globale_non_rinnovabile': r'(\d+(?:[\.,]\d+)?)',
                'indice_prestazione_energetica': r'(\d+(?:[\.,]\d+)?)',
                'distanza_dal_mare': r'(\d+(?:[\.,]\d+)?)\s*metri',
                'anno_costruzione': r'(\d{4})',
            }
            
            import re
            for field, pattern in numeric_fields.items():
                if field in item and isinstance(item[field], str):
                    match = re.search(pattern, item[field])
                    if match:
                        # Handle number formatting (replace comma with dot for decimal separator)
                        value = match.group(1).replace('.', '').replace(',', '.')
                        try:
                            item[field] = float(value)
                            # Convert to int if it's a whole number
                            if field in ['anno_costruzione']:
                                item[field] = int(float(value))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Could not convert {field} value '{value}' to number")
            
            # Process integer fields (room counts, floors, etc.)
            count_fields = ['locali', 'bagni', 'camere_da_letto', 'camere', 'piani_edificio', 'piano', 
                           'totale_piani_edificio', 'posti_auto', 'num_unita']
            for field in count_fields:
                if field in item and isinstance(item[field], str):
                    # Try to extract the first number from the string
                    match = re.search(r'(\d+)', item[field])
                    if match:
                        try:
                            item[field] = int(match.group(1))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Could not convert {field} value to integer")
            
            # Clean up description: join multiple parts and strip whitespace
            if 'descrizione' in item:
                if isinstance(item['descrizione'], list):
                    item['descrizione'] = ' '.join([part.strip() for part in item['descrizione'] if part.strip()])
                if isinstance(item['descrizione'], str):
                    item['descrizione'] = item['descrizione'].strip()
            
            # Ensure altre_caratteristiche is a list and clean it up
            if 'altre_caratteristiche' in item:
                if not isinstance(item['altre_caratteristiche'], list):
                    item['altre_caratteristiche'] = [item['altre_caratteristiche']]
                # Clean up list items
                item['altre_caratteristiche'] = [caratteristica.strip() for caratteristica in item['altre_caratteristiche'] 
                                               if caratteristica and caratteristica.strip()]
            
            # Process classe_energetica (extract the letter class)
            if 'classe_energetica' in item and isinstance(item['classe_energetica'], str):
                match = re.search(r'Classe\s+([A-G][\+\d]*)', item['classe_energetica'], re.IGNORECASE)
                if match:
                    item['classe_energetica'] = match.group(1).upper()
            
            # Extract coordinates if they're embedded in a script/div
            if 'latitudine' not in item or 'longitudine' not in item:
                map_script = response.xpath("//script[contains(., 'coordinates')]/text()").get()
                if map_script:
                    lat_match = re.search(r'"lat":\s*([0-9.]+)', map_script)
                    lng_match = re.search(r'"lng":\s*([0-9.]+)', map_script)
                    if lat_match and lng_match:
                        item['latitudine'] = float(lat_match.group(1))
                        item['longitudine'] = float(lng_match.group(1))
            
            # Yield the fully processed item
            yield item
            
        except Exception as e:
            self.logger.error(f"Error parsing announce page: {e}", exc_info=True)
            # In case of error, try to yield the basic item from the list page as fallback
            if 'item' in response.meta:
                self.logger.info(f"Yielding list page item as fallback for {response.url}")
                yield response.meta['item']