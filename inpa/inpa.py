import requests, json
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import logging

logging.basicConfig(level=logging.INFO)


class INPAScraper:
    def __init__(self, headers=None) -> None:
        self.baseurl = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area"
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'it_IT',
            'Access-Control-Allow-Origin': '*',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'portale.inpa.gov.it',
            'Origin': 'https://www.inpa.gov.it',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
            'sec-ch-ua': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        if headers:
            self.headers.update(headers)
        self.setupHTTPSession()
    
    def setupHTTPSession(self):
        self.s = requests.Session()
        self.s.headers = self.headers
        
        # Define the retry strategy
        retry_strategy = Retry(
            total=4,  # Maximum number of retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        )
        # Create an HTTP adapter with the retry strategy and mount it to session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.s.mount("https://", adapter)
    
    def search(self, size=10, **kwargs):
        url = f"{self.baseurl}/search-better"
        payload = {
            "text": "",        # testo di ricerca
            "status": ["OPEN"],      
            "regioneId": None,       # Liguria è "8"
            "categoriaId": None,
            "settoreId": None, 
            "dateFrom": None,
            "dateTo": None, 
            "livelliAnzianitaIds": None, 
            "tipoImpiegoId": None, 
            "salaryMin": None, 
            "salaryMax": None
        }
        payload.update(kwargs)
        data = []
        exit = False
        page = 0
        while not exit:
            logging.info(f"fetching results for page {page}")
            r = self.s.post(url, json=payload, params={
                "page": page, "size": size
            })
            logging.info(f"status code {r.status_code}")
            r.raise_for_status()
            r = r.json()
            data.extend(r["content"])
            page += 1
            exit = r["last"]
        return data


if __name__ == '__main__':
    inpa = INPAScraper()
    results = inpa.search(regioneId="8", status=["CLOSED"])
    with open("results.json", "w") as stream:
        json.dump(results, stream, indent=2)
    