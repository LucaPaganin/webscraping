from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


if __name__ == "__main__":
    # Set up the Chrome WebDriver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Open the URL
        url = "https://immobiliare.it"  # Replace with the desired URL
        driver.get(url)

        # Perform actions on the page if needed
        print("Page title is:", driver.title)

    finally:
        # Close the browser after a delay to observe the page
        input("Press Enter to close the browser...")
        driver.quit()