import scrapy
from scrapy.loader import ItemLoader
from immob.items import ImmobItem, ImmobAnnounceItem
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.selector import Selector
import time
import random
import os
import logging


class ImmobitSeleniumSpider(scrapy.Spider):
    name = "immobit_selenium"
    allowed_domains = ["immobiliare.it"]
    
    # Custom settings to optimize for Selenium usage
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # Do not run parallel requests with Selenium
        'DOWNLOAD_DELAY': 3,       # Minimum delay between pages 
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': True,   # Enable cookies for session maintenance
        # Disable middlewares that aren't needed with Selenium
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'immob.middlewares.RandomUserAgentMiddleware': None,
            'immob.middlewares.ImmobDownloaderMiddleware': None,
            'immob.middlewares.CustomRetryMiddleware': None,
        }
    }
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(ImmobitSeleniumSpider, self).__init__(*args, **kwargs)
        self.start_url = start_url
        
        # Configure Selenium options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Remove this for visual debugging
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        
        # Set up a realistic user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        
        # Initialize the Chrome WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Create mapping for property features
        self.sibling_mapping = {
            'data': "Riferimento e Data annuncio",
            'stato': "stato",
            "spese_condominio": "spese condominio",
            "numero_piani": "totale piani edificio",
            "posti_auto": "Posti Auto"
        }
        
        self.logger.info(f"Spider initialized with Selenium driver")
        if start_url:
            self.logger.info(f"Starting with single URL: {start_url}")
    
    def closed(self, reason):
        """Close the Selenium driver when the spider is closed"""
        self.logger.info("Closing Selenium driver")
        if hasattr(self, 'driver'):
            self.driver.quit()
    
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
    
    def start_requests(self):
        # Single URL mode for debugging
        if hasattr(self, 'start_url') and self.start_url:
            # Create a dummy request - Selenium will handle the actual page load
            yield scrapy.Request(
                url="data:,",  # Dummy URL, not actually used
                callback=self.parse_announce_page_selenium,
                dont_filter=True,
                meta={'selenium_url': self.start_url}
            )
            return
        
        # Normal mode - start with listings pages
        start_urls = [
            "https://www.immobiliare.it/affitto-case/savona/"
        ]
        
        # First visit the homepage to establish cookies
        self.logger.info("Visiting homepage to establish cookies")
        self.driver.get("https://www.immobiliare.it/")
        time.sleep(3)  # Wait for homepage to load
        
        # Check for cookie consent popup and accept if present
        # try:
        #     accept_button = WebDriverWait(self.driver, 5).until(
        #         EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        #     )
        #     accept_button.click()
        #     self.logger.info("Accepted cookies")
        #     time.sleep(1)
        # except Exception as e:
        #     self.logger.info(f"No cookie consent popup found or couldn't click: {e}")
        
        # After homepage and cookie consent, proceed to first listings page
        for url in start_urls:
            # Create a dummy request - our selenium parser will handle the actual loading
            yield scrapy.Request(
                url="data:,",  # Dummy URL, not actually used
                callback=self.parse_selenium,
                dont_filter=True,
                meta={'selenium_url': url}
            )
    
    def parse_selenium(self, response):
        """
        Use Selenium to load and parse the listings page
        """
        url = response.meta['selenium_url']
        self.logger.info(f"Loading listings page with Selenium: {url}")
        
        try:
            # Load the page with Selenium
            self.driver.get(url)
            time.sleep(random.uniform(3.0, 5.0))  # Wait for page to load
            
            # Check if we were blocked or got a captcha
            page_source = self.driver.page_source
            if "captcha" in page_source.lower() or "robot" in page_source.lower():
                self.logger.error(f"CAPTCHA or anti-bot detected on {url}")
                self.save_debug_page(page_source, "captcha_detected")
                return
            
            # Create a Scrapy selector from the Selenium page source
            sel = Selector(text=page_source)
            
            # Process listings the same way as in the original spider
            announcement_items = sel.css("li.nd-list__item.in-searchLayoutListItem")
            self.logger.info(f"Found {len(announcement_items)} listings")
            
            # Process each listing
            for item_selector in announcement_items:
                loader = ItemLoader(item=ImmobAnnounceItem(), selector=item_selector)
                loader.add_css('title', 'a.in-listingCardTitle::attr(title)')
                loader.add_css('prezzo_lista_preview', '.in-listingCardPrice span::text')
                loader.add_css('prezzo', '.in-listingCardPrice span::text')
                loader.add_css('url', 'a.in-listingCardTitle::attr(href)')
                loader.add_css('immagine_lista_preview', 'img::attr(src)')
                loader.add_css('caratteristiche_lista_preview', '.in-listingCardFeatureList__item span::text')
                
                # Map caratteristiche
                caratteristiche_lista_raw = item_selector.css('.in-listingCardFeatureList__item span::text').getall()
                caratteristiche_mapped = self.map_caratteristiche(caratteristiche_lista_raw)
                
                # Add each mapped field to the loader
                for field, value in caratteristiche_mapped.items():
                    if value is not None:
                        loader.add_value(field, value)
                
                # Load all fields
                announce_item = loader.load_item()
                
                # Fix URL to be absolute and set ID
                if 'url' in announce_item and announce_item['url']:
                    full_url = response.urljoin(announce_item['url'])
                    announce_item['url'] = full_url
                    announce_item['id'] = full_url.rstrip("/").split("/")[-1]
                else:
                    full_url = None
                    announce_item['id'] = None
                
                # If we have a detail URL, visit it to get full details
                if full_url:
                    # Use a dummy request with Selenium handling the actual page load
                    yield scrapy.Request(
                        url="data:,",  # Dummy URL, not actually used
                        callback=self.parse_announce_page_selenium,
                        dont_filter=True,
                        meta={
                            'selenium_url': full_url,
                            'item': announce_item
                        }
                    )
                else:
                    # If we couldn't get a detail URL, yield the basic item
                    self.logger.warning(f"No detail URL found for a listing")
                    yield announce_item
            
            # Check for next page
            next_page = sel.xpath("//div[@data-cy='pagination-next']//a[@class='in-pagination__item' and @role='link']/@href").get()
            if next_page:
                next_page_url = response.urljoin(next_page)
                self.logger.info(f"Found next page: {next_page_url}")
                
                # Add a longer delay for pagination to avoid detection
                delay = random.uniform(5.0, 8.0)
                self.logger.info(f"Waiting {delay:.1f}s before processing next page")
                time.sleep(delay)
                
                # Yield a dummy request for the next page
                yield scrapy.Request(
                    url="data:,",  # Dummy URL, not actually used
                    callback=self.parse_selenium,
                    dont_filter=True,
                    meta={'selenium_url': next_page_url}
                )
            else:
                self.logger.info(f"Last page reached: {url}")
                
        except Exception as e:
            self.logger.error(f"Error processing listings page {url}: {str(e)}")
    
    def parse_announce_page_selenium(self, response):
        """
        Use Selenium to load and parse the detail page
        """
        url = response.meta['selenium_url']
        self.logger.info(f"Loading detail page with Selenium: {url}")
        
        try:
            # Load the page with Selenium
            self.driver.get(url)
            
            # Wait longer for detail page and add random delay
            time.sleep(random.uniform(4.0, 6.0))
            
            # Check if we were blocked or got a captcha
            page_source = self.driver.page_source
            if "captcha" in page_source.lower() or "robot" in page_source.lower():
                self.logger.error(f"CAPTCHA or anti-bot detected on {url}")
                self.save_debug_page(page_source, "captcha_detail_page")
                
                # Yield the basic item as fallback if we have it
                if 'item' in response.meta:
                    self.logger.info(f"Yielding list page item as fallback for {url}")
                    yield response.meta['item']
                return
            
            # Create a Scrapy selector from the Selenium page source
            sel = Selector(text=page_source)
            
            # Get the item from the list page or create a new one for single URL mode
            if 'item' in response.meta and isinstance(response.meta['item'], dict):
                # Convert dict to ImmobAnnounceItem if needed (for single URL mode)
                if not isinstance(response.meta['item'], scrapy.Item):
                    from immob.items import ImmobAnnounceItem
                    announce_item = ImmobAnnounceItem()
                    announce_item['id'] = response.meta['item'].get('id')
                    announce_item['url'] = url
                else:
                    announce_item = response.meta['item']
            else:
                # Create a new item if none exists
                from immob.items import ImmobAnnounceItem
                announce_item = ImmobAnnounceItem()
                announce_item['id'] = url.rstrip("/").split("/")[-1]
                announce_item['url'] = url
            
            # Create a loader with our item
            loader = ItemLoader(item=announce_item, selector=sel)
            
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
            loader.add_xpath('spese_condominio', prop_xpath.format('Spese condominio'))
            
            # --- BUILDING INFORMATION ---
            loader.add_xpath('anno_costruzione', prop_xpath.format('Anno di costruzione'))
            loader.add_xpath('stato', prop_xpath.format('Stato'))
            loader.add_xpath('riscaldamento', prop_xpath.format('Riscaldamento'))
            loader.add_xpath('climatizzazione', prop_xpath.format('Climatizzazione'))
            loader.add_xpath('esp_prevalente', prop_xpath.format('Esp. prevalente'))
            
            # --- ENERGY INFORMATION ---
            loader.add_xpath('efficienza_energetica', prop_xpath.format('Efficienza energetica'))
            loader.add_xpath('classe_energetica', prop_xpath.format('Classe energetica'))
            loader.add_xpath('ipe', prop_xpath.format('IPE'))
            
            # --- GARAGE AND PARKING ---
            loader.add_xpath('posti_auto', prop_xpath.format('Posti Auto'))
            loader.add_xpath('garage', prop_xpath.format('Garage'))
            loader.add_xpath('box', prop_xpath.format('Box'))
            
            # --- FINANCIAL AND LEGAL INFORMATION ---
            loader.add_xpath('spese_extra', prop_xpath.format('Spese extra'))
            loader.add_xpath('prezzo_vendita', prop_xpath.format('Prezzo Vendita'))

            # Add any additional fields from the original spider here

            # Load the item with all the extracted data
            item = loader.load_item()
            
            # Yield the complete item
            self.logger.info(f"Successfully extracted detail data for {url}")
            yield item
            
        except Exception as e:
            self.logger.error(f"Error processing detail page {url}: {str(e)}")
            # Try to yield the basic item as fallback
            if 'item' in response.meta:
                yield response.meta['item']
    
    def save_debug_page(self, html_content, prefix="debug"):
        """Save HTML content to a file for debugging"""
        try:
            debug_dir = os.path.join(self.settings.get('JSON_OUTPUT_DIR', 'output'), 'debug')
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            filename = os.path.join(debug_dir, f"{prefix}_{int(time.time())}.html")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"Debug HTML saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving debug HTML: {str(e)}")
