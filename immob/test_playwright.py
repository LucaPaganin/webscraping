from playwright.sync_api import sync_playwright
import pandas as pd
import time
import random
import re

def human_delay(min_seconds=1, max_seconds=3):
    """Simula un ritardo umano tra le azioni."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

def random_scroll(page):
    """Simula lo scrolling umano."""
    # Scorre la pagina a velocità variabile
    total_height = page.evaluate('document.body.scrollHeight')
    scroll_step = random.randint(300, 700)  # Pixel per ciascun passo di scroll
    
    current_position = 0
    while current_position < total_height:
        scroll_amount = min(scroll_step, total_height - current_position)
        page.evaluate(f'window.scrollBy(0, {scroll_amount})')
        current_position += scroll_amount
        
        # Pausa tra gli scroll di durata variabile
        human_delay(0.5, 1.5)

def accetta_cookies(page):
    """Gestisce il banner dei cookie se presente."""
    try:
        # Attendi che il banner dei cookie sia visibile
        cookie_banner = page.wait_for_selector("button#didomi-notice-agree-button", timeout=10000)
        if cookie_banner:
            # Simula un breve ritardo prima di cliccare il pulsante
            human_delay(1, 2)
            cookie_banner.click()
            print("Cookie accettati con successo")
            human_delay(1, 2)  # Attendi che il banner scompaia
    except Exception as e:
        print(f"Banner dei cookie non trovato o già accettato: {e}")

def estrai_informazioni_annunci(page):
    """Estrae le informazioni degli annunci immobiliari dalla pagina."""
    annunci = []
    
    try:
        # Attendi che gli annunci siano caricati - adattato per casa.it
        page.wait_for_selector("article.srp-card", timeout=10000)
        
        # Simula uno scroll umano per caricare tutti gli annunci
        random_scroll(page)
        
        # Trova tutti gli elementi degli annunci
        elementi_annunci = page.query_selector_all("article.srp-card")
        print(f"Trovati {len(elementi_annunci)} annunci")
        
        for annuncio in elementi_annunci:
            # Simula un breve ritardo tra l'elaborazione di annunci diversi
            human_delay(0.5, 1.5)
            
            try:
                # Estrai le informazioni di base di ogni annuncio
                dati_annuncio = {}
                
                # Titolo
                try:
                    titolo_element = annuncio.query_selector("h3")
                    dati_annuncio["titolo"] = titolo_element.inner_text().strip() if titolo_element else "N/D"
                except Exception:
                    dati_annuncio["titolo"] = "N/D"
                
                # Prezzo
                try:
                    prezzo_element = annuncio.query_selector("div.price")
                    dati_annuncio["prezzo"] = prezzo_element.inner_text().strip() if prezzo_element else "N/D"
                except Exception:
                    dati_annuncio["prezzo"] = "N/D"
                
                # Indirizzo
                try:
                    indirizzo_element = annuncio.query_selector("p.address")
                    dati_annuncio["indirizzo"] = indirizzo_element.inner_text().strip() if indirizzo_element else "N/D"
                except Exception:
                    dati_annuncio["indirizzo"] = "N/D"
                
                # Caratteristiche (locali, superficie, bagni, etc.)
                caratteristiche = {}
                try:
                    # Casa.it utilizza una struttura diversa per le caratteristiche
                    features_container = annuncio.query_selector("div.features-container")
                    if features_container:
                        # Locali
                        locali_element = features_container.query_selector("div.feature-rooms span")
                        if locali_element:
                            caratteristiche["locali"] = locali_element.inner_text().strip()
                        
                        # Superficie
                        superficie_element = features_container.query_selector("div.feature-surface span")
                        if superficie_element:
                            caratteristiche["superficie"] = superficie_element.inner_text().strip()
                        
                        # Bagni
                        bagni_element = features_container.query_selector("div.feature-bathrooms span")
                        if bagni_element:
                            caratteristiche["bagni"] = bagni_element.inner_text().strip()
                            
                        # Piano
                        piano_element = features_container.query_selector("div.feature-floor span")
                        if piano_element:
                            caratteristiche["piano"] = piano_element.inner_text().strip()
                    
                    dati_annuncio["caratteristiche"] = caratteristiche
                except Exception as e:
                    print(f"Errore nell'estrazione delle caratteristiche: {e}")
                    dati_annuncio["caratteristiche"] = {}
                
                # Link all'annuncio
                try:
                    link_element = annuncio.query_selector("a.card-link")
                    if link_element:
                        # Casa.it potrebbe usare URL relativi, quindi controlliamo
                        href = link_element.get_attribute("href")
                        if href.startswith("http"):
                            dati_annuncio["link"] = href
                        else:
                            dati_annuncio["link"] = f"https://www.casa.it{href}"
                    else:
                        dati_annuncio["link"] = "N/D"
                except Exception:
                    dati_annuncio["link"] = "N/D"
                
                # Agenzia o Privato
                try:
                    agenzia_element = annuncio.query_selector("div.advertiser-name")
                    dati_annuncio["agenzia"] = agenzia_element.inner_text().strip() if agenzia_element else "N/D"
                except Exception:
                    dati_annuncio["agenzia"] = "N/D"
                
                # Aggiungi l'annuncio alla lista
                annunci.append(dati_annuncio)
            except Exception as e:
                print(f"Errore nell'estrazione dei dati di un annuncio: {e}")
                continue
                
    except Exception as e:
        print(f"Errore durante l'estrazione degli annunci: {e}")
    
    return annunci

def main():
    url = "https://www.casa.it/affitto/residenziale/savona/"
    
    with sync_playwright() as playwright:
        # Randomizza il lancio del browser per assomigliare più a un utente umano
        browser_types = [playwright.chromium, playwright.firefox]
        browser_type = random.choice(browser_types)
        
        # Opzioni per sembrare più umano
        browser = browser_type.launch(
            headless=False,  # Visibile per debug, impostare a True per produzione
            slow_mo=random.randint(50, 150)  # Rallenta le azioni del browser
        )
        
        # Crea un contesto con dimensioni dello schermo realistiche
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Crea una nuova pagina
        page = context.new_page()
        
        try:
            print(f"Apertura URL: {url}")
            page.goto(url)
            
            # Simula un leggero ritardo dopo il caricamento della pagina
            human_delay(2, 4)
            
            # Gestisci il banner dei cookie
            accetta_cookies(page)
            
            # Simula un'interazione umana con la pagina
            random_scroll(page)
            
            # Estrai informazioni dagli annunci
            annunci = estrai_informazioni_annunci(page)
            
            # Stampa i risultati
            print(f"\nRisultati del web scraping ({len(annunci)} annunci):")
            for i, annuncio in enumerate(annunci, 1):
                print(f"\nAnnuncio {i}:")
                print(f"Titolo: {annuncio['titolo']}")
                print(f"Prezzo: {annuncio['prezzo']}")
                print(f"Indirizzo: {annuncio['indirizzo']}")
                print(f"Agenzia: {annuncio.get('agenzia', 'N/D')}")
                
                if annuncio['caratteristiche']:
                    print("Caratteristiche:")
                    for k, v in annuncio['caratteristiche'].items():
                        print(f"  - {k}: {v}")
                
                print(f"Link: {annuncio['link']}")
            
            # Salva i risultati in un file CSV
            if annunci:
                # Prepara i dati per il DataFrame
                df_data = []
                for annuncio in annunci:
                    row = {
                        'Titolo': annuncio['titolo'],
                        'Prezzo': annuncio['prezzo'],
                        'Indirizzo': annuncio['indirizzo'],
                        'Agenzia': annuncio.get('agenzia', 'N/D'),
                        'Link': annuncio['link']
                    }
                    
                    # Aggiungi le caratteristiche come colonne separate
                    if 'caratteristiche' in annuncio and annuncio['caratteristiche']:
                        for k, v in annuncio['caratteristiche'].items():
                            row[k.capitalize()] = v
                    
                    df_data.append(row)
                
                # Crea e salva il DataFrame
                df = pd.DataFrame(df_data)
                df.to_csv('annunci_casa_savona.csv', index=False)
                print("\nI dati sono stati salvati nel file 'annunci_casa_savona.csv'")
            
        except Exception as e:
            print(f"Errore durante l'esecuzione: {e}")
        finally:
            # Pausa finale per sembrare più umano
            human_delay(1, 3)
            
            # Acquisisce uno screenshot prima di chiudere
            page.screenshot(path="casa_it_screenshot.png")
            print("Screenshot salvato come 'casa_it_screenshot.png'")
            
            # Chiudi il browser
            browser.close()
            print("\nScraping completato.")

if __name__ == "__main__":
    main()