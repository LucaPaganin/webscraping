import time
import csv
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager

def human_pause(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

# Configura Chrome con User-Agent random e referer
ua = UserAgent()
user_agent = ua.random
referer = "https://www.google.com"

options = Options()
options.add_argument(f"user-agent={user_agent}")
options.add_argument(f"--referer={referer}")
options.add_argument("--disable-blink-features=AutomationControlled")

# Avvia WebDriver
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

# STEP 1 - Vai alla homepage
driver.get("https://www.immobiliare.it/")
human_pause()

# STEP 2 - Digita "Savona" e seleziona "Affitta"
search_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
search_input.send_keys("Savona")
human_pause()

search_input.send_keys(Keys.RETURN)
human_pause(2, 4)

# STEP 3 - Clicca su "Affitto" tab se presente
try:
    rent_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'affitto')]")))
    rent_tab.click()
    human_pause()
except:
    print("Scheda affitto già selezionata o non trovata.")

# STEP 4 - Clicca su cerca (o invio già fatto)
# Skip (il return della barra già cerca)

# CSV output
with open("annunci_savona.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Titolo", "Prezzo", "Descrizione", "Caratteristiche", "Link"])

    while True:
        human_pause(2, 5)

        # STEP 5 - Trova link agli annunci
        annunci = driver.find_elements(By.CSS_SELECTOR, 'a[data-cy="listing-item-link"]')
        links = [a.get_attribute("href") for a in annunci]

        for link in links:
            try:
                driver.get(link)
                human_pause(2, 4)

                # STEP 6 - Scraping singolo annuncio
                titolo = driver.title
                try:
                    prezzo = driver.find_element(By.CSS_SELECTOR, '[data-cy="ad-price"]').text
                except:
                    prezzo = "N/A"

                try:
                    descrizione = driver.find_element(By.CSS_SELECTOR, '[data-cy="ad-description"]').text
                except:
                    try:
                        descrizione = driver.find_element(By.CSS_SELECTOR, '.in-read__content').text
                    except:
                        descrizione = "N/A"

                caratteristiche = []
                caratteristiche_elems = driver.find_elements(By.CSS_SELECTOR, '[data-cy^="ad-"]')
                for elem in caratteristiche_elems:
                    caratteristiche.append(elem.text)

                writer.writerow([titolo, prezzo, descrizione, "; ".join(caratteristiche), link])
                print(f"✔ Scraping: {titolo}")

            except Exception as e:
                print(f"Errore su annuncio: {e}")
                continue

        # STEP 7 - Vai alla pagina successiva
        try:
            next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[aria-label="Pagina successiva"]')))
            next_btn.click()
        except:
            print("📌 Fine annunci.")
            break

driver.quit()
