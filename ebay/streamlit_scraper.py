import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import os
import time
import random
import re # Import regular expression library for price cleaning
from pathlib import Path # To handle file paths robustly
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging # Importa il modulo logging

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
SAVE_DIR = Path("ebay_results")
SAVE_DIR.mkdir(exist_ok=True) # Create directory if it doesn't exist

# --- Functions ---

def clean_price(price_text):
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

# Configurazione base del logging (opzionale, ma consigliata)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__) # Ottieni un logger per questo modulo

# --- Classe Retry Personalizzata con Logging ---
class LoggingRetry(Retry):
    """
    Una sottoclasse di Retry che aggiunge un log quando un retry
    viene attivato a causa di uno status code nella status_forcelist.
    """
    def increment(self, method=None, url=None, response=None, error=None, _pool=None, _stacktrace=None):
        """
        Sovrascrive il metodo increment per aggiungere il logging.
        """
        # Chiama prima il metodo originale per ottenere la nuova istanza di Retry
        # e per far eseguire la logica di base (es. controllo numero tentativi)
        new_retry = super().increment(method, url, response, error, _pool, _stacktrace)

        # Controlla se il retry è stato attivato da una risposta
        # e se lo status code è nella lista di quelli forzati
        if response and response.status in self.status_forcelist:
            # Calcola il numero del tentativo attuale (considerando che new_retry ha il conteggio decrementato)
            # Se self.total era 5 e new_retry.total è 4, questo è il primo retry (tentativo 1)
            retry_count = (self.total - new_retry.total) if new_retry.total is not None else self.total
            log.warning(
                f"Retry {retry_count}/{self.total} attivato per {method} {url} "
                f"a causa dello status code: {response.status}. "
                f"Prossima attesa: {new_retry.get_backoff_time():.2f}s"
            )
            # Puoi aggiungere qui altri dettagli utili dal response se necessario
            # log.debug(f"Response headers: {response.headers}")

        # Aggiungi log anche per errori (non solo status code) se necessario
        elif error:
             retry_count = (self.total - new_retry.total) if new_retry.total is not None else self.total
             log.warning(
                 f"Retry {retry_count}/{self.total} attivato per {method} {url} "
                 f"a causa di un errore: {error}. "
                 f"Prossima attesa: {new_retry.get_backoff_time():.2f}s"
             )

        return new_retry # Restituisci la nuova istanza di Retry come richiesto

# --- Funzione per Creare la Sessione ---
def create_session_with_retries(
    total_retries=5,
    backoff_factor=0.5, # Fattore di backoff (es. 0.5 -> attese: 0s, 1s, 2s, 4s, 8s)
    status_forcelist=(500, 502, 503, 504), # Codici di stato HTTP che attivano il retry
    allowed_methods=["HEAD", "GET", "OPTIONS", "PUT", "DELETE", "POST"] # Metodi che permettono retry
):
    """
    Crea e configura un oggetto requests.Session con una strategia di retry personalizzata
    che include il logging.

    Args:
        total_retries (int): Numero totale di tentativi da effettuare (inclusa la prima richiesta).
        backoff_factor (float): Fattore usato per calcolare l'attesa tra i tentativi.
                                L'attesa sarà: {backoff factor} * (2 ** ({numero tentativo} - 1)).
        status_forcelist (tuple): Tupla di codici di stato HTTP che forzano un retry.
        allowed_methods (list): Lista di metodi HTTP per cui abilitare i retry.

    Returns:
        requests.Session: Un oggetto sessione configurato con la strategia di retry.
    """
    # 1. Crea l'oggetto LoggingRetry (la nostra classe personalizzata)
    retry_strategy = LoggingRetry(
        total=total_retries,
        status_forcelist=status_forcelist,
        backoff_factor=backoff_factor,
        allowed_methods=allowed_methods,
    )

    # 2. Crea un HTTPAdapter e associa la strategia di retry
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # 3. Crea un oggetto Session
    session = requests.Session()
    
    my_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.ebay.it/', # Adatta questo!
        'Upgrade-Insecure-Requests': '1',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    
    session.headers.update(my_headers) # Aggiungi gli headers alla sessione

    # 4. Monta l'adapter sulla sessione per i prefissi HTTP e HTTPS
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    log.info(f"Sessione creata con {total_retries} retries totali, backoff_factor={backoff_factor}")
    log.info(f"Attese approssimative tra i tentativi (secondi):")
    # Calcola e logga le attese previste
    temp_retry = retry_strategy.new() # Crea una copia temporanea per calcolare i backoff
    # Il primo tentativo non ha attesa precedente
    log.info(f"  - Dopo tentativo 0: 0.00s")
    for i in range(1, total_retries): # Itera per i tentativi di retry (dal 1 al total_retries-1)
         # Simula l'incremento SENZA passare una response fittizia
         # per far avanzare lo stato interno e calcolare il backoff successivo
         temp_retry = temp_retry.increment()
         delay = temp_retry.get_backoff_time()
         log.info(f"  - Dopo tentativo {i}: {delay:.2f}s")


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
            price = clean_price(price_text)

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

def run_scraper(query, max_pages, force_rerun=False):
    """Runs the scraper for the given query and number of pages."""
    sanitized_query = "".join(c if c.isalnum() else "_" for c in query)
    filename = SAVE_DIR / f"{sanitized_query}.csv"

    if not force_rerun and filename.exists():
        st.info(f"File '{filename}' già esistente. Caricamento dati esistenti...")
        try:
            df = pd.read_csv(filename)
            # Ensure Price column is numeric after loading
            if 'Prezzo' in df.columns:
                df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce')
                df.dropna(subset=['Prezzo'], inplace=True) # Remove rows where price couldn't be converted
            return df
        except Exception as e:
            st.error(f"Errore nel caricamento o elaborazione del file CSV '{filename}': {e}")
            st.warning("Procedo con un nuovo scraping.")
            # If loading fails, proceed to scrape anew, potentially overwriting later

    all_listings = []
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

    try:
        df.to_csv(filename, index=False)
        st.success(f"Dati salvati con successo in '{filename}'")
    except Exception as e:
        st.error(f"Impossibile salvare il file CSV '{filename}': {e}")
        # Still return the dataframe for display if saving failed
    return df


# --- Multi-page Setup with Streamlit Pages Dropdown ---
st.set_page_config(layout="wide")  # Use wider layout
st.sidebar.title("Navigazione")
page = st.sidebar.selectbox("Seleziona una pagina:", ["Scraping e Analisi", "Analisi e Filtri", "Chatbot"])

def scraping_and_analysis_page():
    """Page logic for Scraping and Analysis."""
    st.header("🔍 Scraping e Analisi")
    st.title("📊 Web Scraper eBay & Analisi Prezzi")
    st.markdown("""
    Questa applicazione effettua lo scraping dei risultati di ricerca da **eBay.it** per una data query,
    salva i dati in un file CSV e visualizza un'analisi dei prezzi.
    """)

    # --- Input Section ---
    query = st.text_input("Inserisci la query di ricerca per eBay:", placeholder="Es: scheda video nvidia")
    max_pages_to_scrape = st.slider("Numero massimo di pagine da analizzare:", min_value=1, max_value=100, value=10, step=1,
                                    help="Imposta quante pagine di risultati vuoi analizzare. Più pagine richiedono più tempo.")
    start_button = st.button("Avvia Ricerca / Carica Dati")
    force_rerun = st.checkbox("Forza nuovo scraping anche se il file esiste", value=False, 
                              help="Seleziona per forzare un nuovo scraping anche se il file CSV esiste già.")
    if start_button and query:
        with st.spinner(f"Elaborazione per '{query}'... Attendere prego."):
            results_df = run_scraper(query, max_pages_to_scrape, force_rerun)

        if results_df is not None and not results_df.empty:
            st.subheader(f"📈 Analisi dei Prezzi per '{query}'")
            if 'Prezzo' in results_df.columns and pd.api.types.is_numeric_dtype(results_df['Prezzo']) and results_df['Prezzo'].notna().sum() > 0:
                mean_price = results_df['Prezzo'].mean()
                max_price = results_df['Prezzo'].max()
                min_price = results_df['Prezzo'].min()
                median_price = results_df['Prezzo'].median()
                std_dev_price = results_df['Prezzo'].std()

                st.metric("Prezzo Medio", f"€ {mean_price:,.2f}")
                st.metric("Prezzo Mediano", f"€ {median_price:,.2f}")
                st.metric("Deviazione Standard Prezzi", f"€ {std_dev_price:,.2f}")
                st.metric("Prezzo Minimo", f"€ {min_price:,.2f}")
                st.metric("Prezzo Massimo", f"€ {max_price:,.2f}")

                fig = px.histogram(results_df, x='Prezzo', nbins=30,
                                    title=f"Distribuzione dei Prezzi per '{query}'",
                                    labels={'Prezzo': 'Prezzo (€)'},
                                    opacity=0.8,
                                    color_discrete_sequence=px.colors.qualitative.Pastel)

                fig.add_vline(x=mean_price, line_dash="dash", line_color="red", annotation_text=f"Media: {mean_price:.2f}€")
                fig.add_vline(x=median_price, line_dash="dot", line_color="green", annotation_text=f"Mediana: {median_price:.2f}€")

                fig.update_layout(
                    bargap=0.1,
                    xaxis_title="Prezzo (€)",
                    yaxis_title="Numero di Annunci",
                    title_x=0.5
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("La colonna 'Prezzo' non è presente, non è numerica o non contiene dati validi per generare il grafico.")

            st.subheader(f"📄 Tabella dei Risultati per '{query}'")
            results_df_display = results_df.copy()
            if 'Prezzo' in results_df_display.columns:
                results_df_display['Prezzo'] = results_df_display['Prezzo'].apply(lambda x: f"€ {x:,.2f}" if pd.notna(x) else "N/D")
            st.dataframe(results_df_display, use_container_width=True, hide_index=True)
        elif start_button and query:
            st.error("Non è stato possibile ottenere o caricare dati validi per la query specificata.")
    elif start_button and not query:
        st.warning("Per favore, inserisci una query di ricerca.")

def analysis_and_filters_page():
    """Page logic for Analysis and Filters."""
    st.header("📂 Analisi e Filtri")
    uploaded_file = st.file_uploader("Carica un file CSV con i dati da analizzare:", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if 'Prezzo' in df.columns:
                df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce')
                df.dropna(subset=['Prezzo'], inplace=True)
            st.success("File caricato con successo!")
            
            # Extract the last part of the URL before the query string and create a new column 'id_inserzione'
            df['id_inserzione'] = df['Link'].apply(lambda x: x.split('?')[0].split('/')[-1] if isinstance(x, str) else None)

            # Drop duplicates based on the 'id_inserzione' column
            df.drop_duplicates(subset=['id_inserzione'], inplace=True)
            st.markdown(f"**Dati unici dopo rimozione duplicati:** {len(df)} record")
            st.subheader(f"📄 Tabella dei Dati Caricati: {len(df)} record")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            min_price = float(df['Prezzo'].min())
            max_price = float(df['Prezzo'].max())

            st.subheader("📊 Filtri e Grafici")
            st.write("Applica filtri per analizzare i dati in modo più dettagliato.")
            st.write("Puoi filtrare per prezzo, parole chiave nel titolo e altre caratteristiche.")
            
            min_price, max_price = st.slider(
                "Filtra per Prezzo (€):", 
                min_value=min_price, 
                max_value=max_price, 
                value=(min_price, max_price),
                step=1.0
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("Filtri per Parole Chiave nel **Titolo**:")
                keyword_filter = st.text_input(
                    "Filtra per Parole Chiave nel Titolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )
                exclude_keyword_filter = st.text_input(
                    "Escludi Parole Chiave nel Titolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )
            
            with col2:
                st.markdown("Filtri per Parole Chiave nel **Sottotitolo**:")
                subtitle_keyword_filter = st.text_input(
                    "Filtra per Parole Chiave nel Sottotitolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )
                exclude_subtitle_keyword_filter = st.text_input(
                    "Escludi Parole Chiave nel Sottotitolo:", 
                    placeholder="Inserisci una o più parole chiave separate da spazi"
                )

            # Applica i filtri al dataframe
            filtered_df = df[(df['Prezzo'] >= min_price) & (df['Prezzo'] <= max_price)]

            def extract_keywords(input_string):
                """Extract keywords from a string, keeping quoted groups together."""
                matches = re.findall(r'"(.*?)"|(\S+)', input_string.lower())
                return [kw[0] or kw[1] for kw in matches]  # Flatten the tuple results

            if keyword_filter:
                keywords = extract_keywords(keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Titolo'].str.lower().apply(
                        lambda title: all(keyword in title for keyword in keywords)
                    )
                ]
            if exclude_keyword_filter:
                exclude_keywords = extract_keywords(exclude_keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Titolo'].str.lower().apply(
                        lambda title: not any(keyword in title for keyword in exclude_keywords)
                    )
                ]
            
            if subtitle_keyword_filter:
                subtitle_keywords = extract_keywords(subtitle_keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Sottotitolo'].str.lower().apply(
                        lambda subtitle: all(keyword in subtitle for keyword in subtitle_keywords)
                    )
                ]
            if exclude_subtitle_keyword_filter:
                exclude_subtitle_keywords = extract_keywords(exclude_subtitle_keyword_filter)
                filtered_df = filtered_df[
                    filtered_df['Sottotitolo'].str.lower().apply(
                        lambda subtitle: not any(keyword in subtitle for keyword in exclude_subtitle_keywords)
                    )
                ]

            st.write(f"Risultati filtrati: {len(filtered_df)} su {len(df)} totali")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            fig = px.histogram(filtered_df, x='Prezzo', nbins=30,
                                title="Distribuzione dei Prezzi Filtrati",
                                labels={'Prezzo': 'Prezzo (€)'},
                                opacity=0.8,
                                color_discrete_sequence=px.colors.qualitative.Pastel)
            if not filtered_df.empty:
                mean_price = filtered_df['Prezzo'].mean()
                median_price = filtered_df['Prezzo'].median()

                fig.add_vline(x=mean_price, line_dash="dash", line_color="red", annotation_text=f"Media: {mean_price:.2f}€")
                fig.add_vline(x=median_price, line_dash="dot", line_color="green", 
                              annotation_text=f"Mediana: {median_price:.2f}€", annotation_position="bottom")
                
                std_dev_price = filtered_df['Prezzo'].std()
                fig.add_vline(x=mean_price - 1 * std_dev_price, line_dash="dash", line_color="gold", 
                              annotation_text=f"Media - 1σ: {mean_price - 1 * std_dev_price:.2f}€", annotation_position="top")
                fig.add_vline(x=mean_price + 1 * std_dev_price, line_dash="dash", line_color="gold", 
                              annotation_text=f"Media + 1σ: {mean_price + 1 * std_dev_price:.2f}€", annotation_position="top")
                fig.add_vline(x=mean_price + 2 * std_dev_price, line_dash="dash", line_color="blue", 
                              annotation_text=f"Media + 2σ: {mean_price + 2 * std_dev_price:.2f}€", annotation_position="top")
                fig.add_vline(x=mean_price + 3 * std_dev_price, line_dash="dash", line_color="purple", 
                              annotation_text=f"Media + 3σ: {mean_price + 3 * std_dev_price:.2f}€", annotation_position="top")
            
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Errore durante il caricamento o l'elaborazione del file: {e}")

def chatbot_page():
    """Placeholder for Chatbot page."""
    st.header("🤖 Chatbot")
    st.write("Questa pagina è in fase di sviluppo. Prossimamente sarà disponibile un chatbot interattivo.")

# --- Page Routing ---
if page == "Scraping e Analisi":
    scraping_and_analysis_page()
elif page == "Analisi e Filtri":
    analysis_and_filters_page()
elif page == "Chatbot":
    chatbot_page()
