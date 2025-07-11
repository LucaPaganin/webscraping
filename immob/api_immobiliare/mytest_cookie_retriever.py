
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# --- Start undetected Chrome browser ---
options = uc.ChromeOptions()
options.add_argument('--lang=it-IT')
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-infobars')
options.add_argument('--disable-extensions')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')

driver = uc.Chrome(options=options)


url = "https://www.immobiliare.it/"
driver.get(url)

wait = WebDriverWait(driver, 20)

# --- Captcha detection and manual solving ---
def is_captcha_present():
    try:
        # Datadome captcha usually has an iframe or div with datadome or captcha in id/class
        driver.find_element(By.XPATH, "//*[contains(@id, 'datadome') or contains(@class, 'datadome') or contains(@id, 'captcha') or contains(@class, 'captcha')]")
        return True
    except Exception:
        return False

# Wait for captcha to be solved if present
if is_captcha_present():
    print("[INFO] Captcha detected! Please solve it manually in the browser window...")
    while is_captcha_present():
        time.sleep(2)
    print("[INFO] Captcha solved. Continuing automation...")

# Accept cookies if popup appears
try:
    accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ACCETTA', 'accetta'), 'accetta')]")))
    accept_btn.click()
    time.sleep(1)
except Exception:
    pass

# Find the search bar and enter 'Savona'
search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Cerca città']")))
search_input.clear()
search_input.send_keys("Savona")
time.sleep(1)
search_input.send_keys(Keys.RETURN)

# Wait for the results dropdown and click the first result
first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul[role='listbox'] li, ul[role='listbox'] a")))
first_result.click()

# Wait for the page to load (e.g., listings or city page)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

# Optionally, keep the browser open for a few seconds to see the result
time.sleep(5)
driver.quit()
