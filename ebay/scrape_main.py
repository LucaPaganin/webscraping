import logging
from datetime import datetime
from pathlib import Path
from ebay_scraper import EbayScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelName)s] %(message)s")

if __name__ == '__main__':
    what = "pkmn"
    
    ps5_url = "https://www.ebay.it/sch/i.html?_from=R40&_nkw=playstation+5&_sacat=0&LH_PrefLoc=98&_ipg=120&imm=1&Modello=Sony%2520PlayStation%25205%2520Blu%252DRay%2520Edition%7CSony%2520PlayStation%25205%2520Digital%2520Edition&_dcat=139971&rt=nc&LH_ItemCondition=3000%7C1500"
    pkmn_url = "https://www.ebay.it/sch/i.html?_from=R40&_nkw=pok%C3%A8mon+game+boy+advance&_sacat=0&_fsrp=1&_ipg=240&rt=nc&Editore=Nintendo&_dcat=139973"
    
    if what == "pkmn":
        start_url = pkmn_url
    else:
        start_url = ps5_url
    
    scraper = EbayScraper()
    data = scraper.navigatePages(start_url)
    
    data.to_csv(Path.home()/f"Downloads/{what}_prices_{datetime.now().strftime('%Y-%m-%d')}.csv")