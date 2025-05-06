import asyncio
import csv
from crawl4ai import AsyncWebCrawler, CrawlResult
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
import pandas as pd
import requests
import random


# Funzione principale per l'estrazione e il salvataggio
async def extract_data_from_url(url, proxy=None):
    # Basic configuration
    strategy = BFSDeepCrawlStrategy(
        max_depth=2,               # Crawl initial page + 2 levels deep
        include_external=False,    # Stay within the same domain
        max_pages=50,              # Maximum number of pages to crawl (optional)
        score_threshold=0.3,       # Minimum score for URLs to be crawled (optional)
    )

    async with AsyncWebCrawler(crawl_strategy=strategy, proxy=proxy) as crawler:
        # Estrai i dati
        
        result: CrawlResult = await crawler.arun(url=url)
        
        md = result.markdown.strip()
        if not md:
            print("No data extracted.")
        else:
            print("Found something!")
        
        links = [l for l in result.links]
        print(links)
    
    
    
                
       
# Esegui l'estrazione e salvataggio
if __name__ == "__main__":
    url = "https://learn.microsoft.com/en-us/collections/50wkaqtq50egz3?ref=collection&listId=60yka7t2o8od52&sharingId=6A9F03F25E12DA9E"
    filename = "result.md"
    asyncio.run(extract_data_from_url(url))
