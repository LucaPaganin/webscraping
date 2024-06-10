import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)

class EbayScraper:
    def __init__(self) -> None:
        # Set up the Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        self.driver = webdriver.Chrome(options=options)
    
    def navigatePages(self, url, pagelim=None):
        page = 1
        alldata = []
        nexturl = url
        while True:
            logger.info(f"visiting page {page}")
            self.visitPage(nexturl)
            pagedata = self.getPageItems()
            alldata.extend(pagedata)
            logger.info(f"looking for next link in page {page}")
            nexturl = self.getNextPageLink()
            if nexturl is None or (pagelim is not None and page >= pagelim):
                logger.info(f"Interrupting navigation at page {page}")
                break
            page += 1
        
        return pd.DataFrame(alldata)
    
    def visitPage(self, url):
        self.driver.get(url)
        try:
            logger.info("started waiting for s-item elements")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 's-item'))
            )
            logger.info("finished waiting for s-item elements")
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-pagination"))
            # )
        except Exception as e:
            logger.error(f"Error or timeout occurred: {e}")
    
    def getPageItems(self):
        items = self.driver.find_elements(By.CSS_SELECTOR, "li.s-item")
        outdata = []
        logger.info(f"Found {len(items)} element in page")
        for item in items:
            link = item.find_element(By.CSS_SELECTOR, "a.s-item__link")
            price = item.find_element(By.CSS_SELECTOR, "span.s-item__price")
            subtitle = item.find_element(By.CSS_SELECTOR, "div.s-item__subtitle")
            title = item.find_element(By.CSS_SELECTOR, "div.s-item__title")
            
            if price and price.text:
                data = {
                    "link": link.get_attribute("href"),
                    "price": price.text,
                    "title": title.text,
                    "subtitle": subtitle.text
                }
                outdata.append(data)
        logger.info(f"Finished processign page elements")
        
        return outdata

    def getNextPageLink(self):
        res = None
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "div.s-pagination nav.pagination a.pagination__next")
            if next_button and next_button.get_attribute("href"):
                res = next_button.get_attribute("href")
                logger.info(f"found link for next page: {res}")
        except NoSuchElementException:
            logger.info(f"no next link found")
        return res
        
    
    