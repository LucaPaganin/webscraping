import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import os
import time
import random
import re 
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# --- Configuration ---
# Fallback User Agents in case fake-useragent fails
FALLBACK_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0',
]

# Try to import fake_useragent, use fallback if it fails
try:
    from fake_useragent import UserAgent

    ua = UserAgent()
    def get_user_agent():
        try:
            return ua.random
        except Exception: # Catch potential errors within fake-useragent
            print("fake-useragent failed to generate, using fallback.")
            return random.choice(FALLBACK_USER_AGENTS)
except ImportError:
    print("fake-useragent not installed. Using fallback user agents.")
    def get_user_agent():
        return random.choice(FALLBACK_USER_AGENTS)

# Directory to save CSV files
SAVE_DIR = Path("scraping_results")
SAVE_DIR.mkdir(exist_ok=True) # Create directory if it doesn't exist

# Basic logging configuration (optional but recommended)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__) # Get a logger for this module

# Make language detection deterministic
DetectorFactory.seed = 42

# Function to detect language
def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return None

# --- Functions ---
def extract_keywords(input_string):
    """Extract keywords from a string, keeping quoted groups together."""
    matches = re.findall(r'"(.*?)"|(\S+)', input_string.lower())
    return [kw[0] or kw[1] for kw in matches]  # Flatten the tuple results

def clean_ebay_price(price_text):
    """Cleans the price string and converts it to a float."""
    if price_text is None:
        return None
    # Remove currency symbols, thousands separators (.), and replace comma decimal separator
    price_text = re.sub(r'[^\d,\.]', '', price_text).replace('.', '').replace(',', '.')
    try:
        # Handle price ranges (e.g., "10.00 a 20.00") - take the first price
        if 'a' in price_text:
            price_text = price_text.split('a')[0].strip()
        return float(price_text)
    except ValueError:
        # Return None if conversion fails after cleaning
        return None

# --- Custom Retry Class with Logging ---
class LoggingRetry(Retry):
    """
    A subclass of Retry that adds logging when a retry
    is triggered due to a status code in the status_forcelist.
    """
    def increment(self, method=None, url=None, response=None, error=None, _pool=None, _stacktrace=None):
        """
        Overrides the increment method to add logging.
        """
        # Call the original method first to get the new Retry instance
        # and to execute the base logic (e.g., checking retry count)
        new_retry = super().increment(method, url, response, error, _pool, _stacktrace)

        # Check if the retry was triggered by a response
        # and if the status code is in the forced list
        if response and response.status in self.status_forcelist:
            # Calculate the current retry count (considering that new_retry has the count decremented)
            # If self.total was 5 and new_retry.total is 4, this is the first retry (attempt 1)
            retry_count = (self.total - new_retry.total) if new_retry.total is not None else self.total
            log.warning(
                f"Retry {retry_count}/{self.total} triggered for {method} {url} "
                f"due to status code: {response.status}. "
                f"Next wait: {new_retry.get_backoff_time():.2f}s"
            )
            # You can add other useful details from the response here if needed
            # log.debug(f"Response headers: {response.headers}")

        # Add logs for errors (not just status codes) if needed
        elif error:
             retry_count = (self.total - new_retry.total) if new_retry.total is not None else self.total
             log.warning(
                 f"Retry {retry_count}/{self.total} triggered for {method} {url} "
                 f"due to an error: {error}. "
                 f"Next wait: {new_retry.get_backoff_time():.2f}s"
             )

        return new_retry # Return the new Retry instance as required

# --- Function to Create the Session ---
def create_session_with_retries(
    total_retries=5,
    backoff_factor=0.5, # Backoff factor (e.g., 0.5 -> waits: 0s, 1s, 2s, 4s, 8s)
    status_forcelist=(500, 502, 503, 504), # HTTP status codes that trigger retry
    allowed_methods=["HEAD", "GET", "OPTIONS", "PUT", "DELETE", "POST"] # Methods that allow retry
):
    """
    Creates and configures a requests.Session object with a custom retry strategy
    that includes logging.

    Args:
        total_retries (int): Total number of attempts to make (including the first request).
        backoff_factor (float): Factor used to calculate wait time between attempts.
                                The wait will be: {backoff factor} * (2 ** ({attempt number} - 1)).
        status_forcelist (tuple): Tuple of HTTP status codes that force a retry.
        allowed_methods (list): List of HTTP methods for which retries are enabled.

    Returns:
        requests.Session: A session object configured with the retry strategy.
    """
    # 1. Create the LoggingRetry object (our custom class)
    retry_strategy = LoggingRetry(
        total=total_retries,
        status_forcelist=status_forcelist,
        backoff_factor=backoff_factor,
        allowed_methods=allowed_methods,
    )

    # 2. Create an HTTPAdapter and associate the retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # 3. Create a Session object
    session = requests.Session()
    
    my_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/', # Adapt this!
        'Upgrade-Insecure-Requests': '1',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    
    session.headers.update(my_headers) # Add headers to the session

    # 4. Mount the adapter on the session for HTTP and HTTPS prefixes
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    log.info(f"Session created with {total_retries} total retries, backoff_factor={backoff_factor}")
    log.info(f"Approximate waits between attempts (seconds):")
    # Calculate and log the expected waits
    temp_retry = retry_strategy.new() # Create a temporary copy to calculate backoff
    # The first attempt has no previous wait
    log.info(f"  - After attempt 0: 0.00s")
    for i in range(1, total_retries): # Iterate for retry attempts (from 1 to total_retries-1)
         # Simulate increment WITHOUT passing a fake response
         # to advance the internal state and calculate the next backoff
         temp_retry = temp_retry.increment()
         delay = temp_retry.get_backoff_time()
         log.info(f"  - After attempt {i}: {delay:.2f}s")

    return session

def scrape_ebay_page(session: requests.Session, url: str) -> tuple:
    """Scrapes a single eBay search results page."""
    listings_data = []
    # Definisci gli header (magari aggiornando User-Agent e Referer dinamicamente)
    try:
        response = session.get(url, timeout=20) # Increased timeout
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all listing items (Update selector if eBay's structure changes)
        # Common container classes: s-item, s-item__wrapper, etc.
        # Using a more general approach that might be more robust
        items = soup.find_all('li', class_=lambda x: x and x.startswith('s-item'))
        if not items: # Fallback selector if the primary one fails
            items = soup.find_all('div', class_='s-item__wrapper')

        if not items:
            st.warning(f"Nessun annuncio trovato sulla pagina con i selettori correnti: {url}")
            return listings_data, None # Return empty list and no next page link

        for item in items:
            title_element = item.find('div', class_='s-item__title')
            title = title_element.get_text(strip=True) if title_element else "N/A"
            # Filter out "Shop on eBay" and similar promotional items which might lack price/link
            if title.lower() in ["shop on ebay", "results matching fewer words"]:
                continue

            subtitle_element = item.find('div', class_='s-item__subtitle')
            subtitle = subtitle_element.get_text(strip=True) if subtitle_element else "" # Empty string if no subtitle

            price_element = item.find('span', class_='s-item__price')
            price_text = price_element.get_text(strip=True) if price_element else None
            price = clean_ebay_price(price_text)

            link_element = item.find('a', class_='s-item__link')
            link = link_element['href'] if link_element else "N/A"
            
            seller_info = item.find('span', class_='s-item__seller-info-text')
            seller = seller_info.get_text(strip=True) if seller_info else "N/A"

            # Only add if essential info is present
            if title != "N/A" and link != "N/A" and price is not None:
                 listings_data.append({
                    'Titolo': title.replace('-- Spedizione GRATUITA', '').strip(), # Clean title
                    'Sottotitolo': subtitle,
                    'Prezzo': price,
                    "Venditore": seller,
                    'Link': link
                })

        # Find the 'Next' page link (Update selector if needed)
        next_page_element = soup.find('a', class_='pagination__next')
        next_page_url = next_page_element['href'] if next_page_element else None

        return listings_data, next_page_url

    except requests.exceptions.RequestException as e:
        st.error(f"Errore durante la richiesta a {url}: {e}")
        return listings_data, None # Return collected data so far, but stop pagination
    except Exception as e:
        st.error(f"Errore durante il parsing della pagina {url}: {e}")
        return listings_data, None # Return collected data so far


def run_ebay_scraper(query, max_pages, start_search_url=None):
    """Runs the scraper for the given query and number of pages."""

    all_listings = []
    if start_search_url:
        current_url = start_search_url
    else:
        # Replace spaces with '+' for the URL query parameter
        search_query_url = query.replace(' ', '+')
        # Construct initial URL for eBay Italy (ebay.it)
        current_url = f"https://www.ebay.it/sch/i.html?_nkw={search_query_url}"

    st.write(f"Inizio scraping per '{query}'...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    referer = None

    for page_num in range(1, max_pages + 1):
        status_text.text(f"Scraping pagina {page_num}/{max_pages}...")
        headers = {
            'User-Agent': get_user_agent(),
        }
        if referer is not None:
            headers['Referer'] = referer # Set the referer header for the next request
        referer = current_url # Update referer for the next iteration
        
        st.caption(f"URL Pagina {page_num}: {current_url}") # Show current URL being scraped
        st.caption(f"User-Agent: {headers['User-Agent']}") # Show UA being used
        
        session = create_session_with_retries()
        session.headers.update(headers) # Set headers for the session

        page_listings, next_page_url = scrape_ebay_page(session, current_url)
        all_listings.extend(page_listings)

        # Update progress bar
        progress = int((page_num / max_pages) * 100)
        progress_bar.progress(progress)

        if not next_page_url:
            st.warning(f"Raggiunto il limite delle pagine o link 'Successivo' non trovato dopo pagina {page_num}.")
            break # Exit loop if no next page

        current_url = next_page_url

        # Basic politeness delay
        time.sleep(random.uniform(2, 5)) # Random delay between 2 and 5 seconds

    progress_bar.progress(100)
    status_text.success(f"Scraping completato! Trovati {len(all_listings)} annunci validi.")

    if not all_listings:
        st.warning("Nessun dato valido raccolto. Impossibile creare il file CSV o i grafici.")
        return None

    # Create DataFrame and save to CSV
    df = pd.DataFrame(all_listings)
    # Ensure Price column is numeric before saving (already done by clean_price)
    df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce')
    df.dropna(subset=['Prezzo'], inplace=True) # Remove rows if price is invalid after all

    if df.empty:
        st.warning("Nessun dato valido con prezzo numerico trovato dopo la pulizia.")
        return None

    return df


def run_vinted_scraper(query, max_pages, start_search_url=None):
    """
    Scrapes search results from vinted.com for a given query using Selenium and returns a DataFrame.
    """

    # Configure Selenium WebDriver
    chrome_options = Options()
    # Remove headless mode to see the browser
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    if not start_search_url:
        base_url = "https://www.vinted.it"
        search_url = f"{base_url}/catalog?search_text={query.replace(' ', '+')}"
    else:
        search_url = start_search_url
    
    results = []

    try:
        for page in range(1, max_pages + 1):
            url = f"{search_url}&page={page}"
            driver.get(url)
            
            # Close the cookie banner if present
            try:
                cookie_reject_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
                )
                cookie_reject_button.click()
                logging.info("Cookie banner closed successfully.")
            except TimeoutException:
                logging.info("Cookie banner not found or already closed.")

            try:
                # Wait for the items to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "feed-grid__item"))
                )
                # Wait for the favorite button elements to be clickable
                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.u-background-white.new-item-box__favourite-icon"))
                    )
                    logging.info("Favorite button elements are clickable.")
                except TimeoutException:
                    logging.warning("Timeout while waiting for favorite button elements to be clickable.")
                
            except TimeoutException:
                logging.warning(f"Timeout while waiting for items on page {page}. Stopping.")
                break

            items = driver.find_elements(By.CLASS_NAME, "feed-grid__item")
            if not items:
                logging.info(f"No more items found on page {page}. Stopping.")
                break

            for item in items:
                try:
                    link_element = item.find_element(By.CSS_SELECTOR, ".new-item-box__image-container > a")
                    href = link_element.get_attribute("href")
                    # Extract title, brand, condition, price, and shipping info from the title attribute
                    textdata = link_element.get_attribute("title")
                    
                    try:
                        *title_parts, brand, condition, price, price_with_shipping = [
                            p.strip() for p in textdata.split(", ") if p.strip()
                        ]
                        title = ",".join(title_parts).strip()
                        brand = brand.split(":")[1].strip() if ":" in brand else brand.strip()
                        condition = condition.split(":")[1].strip() if ":" in condition else condition.strip()
                        
                        # default for title value
                        if not title and brand:
                            title = brand
                        
                        price_shipping, notes = price_with_shipping.split(" ", maxsplit=1)
                    except Exception as e:
                        logging.error(f"Error parsing item textdata: {textdata} - {e}")
                        continue
                    
                    price = price.replace("€", "").replace(",", "").strip()
                    price_shipping = price_shipping.replace("€", "").replace(",", "").strip()
                    
                    try:
                        price = float(price) if price else None
                        price_shipping = float(price_shipping) if price_shipping else None
                    except ValueError:
                        pass
                    
                    # try to retrieve the number of favorites
                    num_favorites = None
                    try:
                        fav_element = item.find_element(
                            By.CSS_SELECTOR, 
                            'button.u-background-white.new-item-box__favourite-icon span[class^="web_ui__Text"]'
                        )
                        if fav_element:
                            num_favorites = fav_element.text.strip()
                            try:
                                num_favorites = int(num_favorites.replace(" ", ""))
                            except ValueError:
                                pass
                    except NoSuchElementException:
                        logging.warning("No favorites element found.")

                    # Append the extracted data to results
                    results.append({
                        "Titolo": title,
                        "Brand": brand,
                        "Condizione": condition,
                        "Prezzo": price,
                        "Preferiti": num_favorites,
                        "Prezzo con spedizione": price_shipping,
                        "Link": href,
                        "Note": notes,
                    })
                except NoSuchElementException as e:
                    logging.error(f"Error parsing item: {e}")

            # Politeness delay
            time.sleep(random.uniform(2, 5))

    except Exception as e:
        logging.error(f"Unexpected error during scraping: {e}")
    finally:
        driver.quit()

    # Convert results to DataFrame    
    df = pd.DataFrame(results)

    return df