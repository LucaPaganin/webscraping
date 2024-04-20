import requests, json


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
    
    def setupHTTPSession(self):
        pass
    
    def searchBetter(self, **kwargs):
        url = f"{self.baseurl}/search-better"
        payload = {
            "text": "camera",        # testo di ricerca
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


if __name__ == '__main__':
    pass

# url di ricerca concorsi
url = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"

# url singolo concorso
# https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/{concorsoId}



r = requests.post(url, 
                  headers=headers, 
                  json=payload, 
                  params={
                      "page": 0,
                      "size": 40
                  })

out = r.json()

with open("out.json", "w") as stream:
    json.dump(out, stream, indent=2)