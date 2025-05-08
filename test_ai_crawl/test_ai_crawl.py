import asyncio
import csv
from crawl4ai import AsyncWebCrawler, CrawlResult, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
import pandas as pd
import requests
import random


async def main():

    async with AsyncWebCrawler() as crawler:
        result: CrawlResult = await crawler.arun(
            url="https://immobiliare.it/affitto-case/savona",
            config=CrawlerRunConfig(
                magic=True,  # Simplifies a lot of interaction
                remove_overlay_elements=True,
                page_timeout=60000
            )
        )
        
        print(result.success)
        print(result.html)
        print(result.markdown)


# Esegui l'estrazione e salvataggio
if __name__ == "__main__":
    asyncio.run(main())
