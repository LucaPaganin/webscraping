import requests

url = "https://www.immobiliare.it/annunci/120679702/"

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Referer": "https://www.immobiliare.it/annunci/120679702/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "sec-ch-device-memory": "8",
    "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-full-version-list": '"Not)A;Brand";v="8.0.0.0", "Chromium";v="138.0.7204.97", "Google Chrome";v="138.0.7204.97"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
}

# I cookie si possono passare come dizionario
cookies = {
    "IMMSESSID": "e463dc3c67fb3bbc2073da5b3b8fcfed",
    "imm_pl": "it",
    "PHPSESSID": "c55ebc0e447b08374ea4def9a17e4baf",
    "datadome": "oZCAJouyQeFs7L9bDJTqp2aOq5lgOLJ0BGOtkUs288e71tW48Tu81BRMCFsFz7lSHpGnBY7WyKf5rc9ps0cadQaWWlX67Y6dUJa4wCE405Hz4Ku31ZfEFC_Zo0z~d9Rn",
}

# response = requests.get(url, headers=headers, cookies=cookies)

from bs4 import BeautifulSoup
import re
import json

with open('scripts/mytest_ad.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all script tags
scripts = soup.find_all('script')

# print(response.status_code)
# print(response.text)
