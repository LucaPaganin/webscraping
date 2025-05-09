from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI
import os

import asyncio

def configure_browser():
    user_data_dir = os.environ['LOCALAPPDATA']+"/Google/Chrome/User Data"
    # Configure the browser to connect to your Chrome instance
    browser = Browser(
        config=BrowserConfig(
            browser_binary_path='C:/Program Files/Google/Chrome/Application/chrome.exe',
            extra_browser_args=[
                "--remote-debugging-port=9222",
                # '--no-sandbox',
                # '--disable-dev-shm-usage',
                # Arguments to avoid bot detection
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '--window-size=1920,1080',
                '--disable-extensions',
                '--disable-notifications',
                '--disable-popup-blocking',
                '--start-maximized',
                # Uncomment if you need a headless browser
                # '--headless=new',  # Modern headless mode that's less detectable
                # Performance options
                '--disable-gpu',
                '--disable-infobars',
                # Use a fake profile to seem more human-like
                '--profile-directory=Default',
                f"--user-data-dir={user_data_dir}"
            ]
        )
    )
    return browser

def configure_agent(browser=None):
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    os.environ['GEMINI_API_KEY'] = GOOGLE_API_KEY

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )

    TASK = """
    Visit the website of immobiliare.it and make a search for renting houses in Savona, Italy.
    Remember to type in the search bar "Savona" and to select the first option appearing in the dropdown.
    After that, select the first two houses appearing in the results and extract the following information:
    - Title
    - Price
    - Description
    - All characteristics you find in the features area
    - Link to the house. You can find it in the address bar of the browser when you go to the house page.
    
    Expect that the page will be in Italian. Also, dialog windows may appear asking if you want to save your search or to add the house to your favorites.
    If they appear, do not worry about them: simply close them and continue. The dialogs may appear either in the listing page or in the house page.
    If you are asked to log in, please do not log in. Just close the dialog and continue.
    Remember to simulate human behavior by waiting a few seconds before clicking on the house.
    Do not be too fast or too slow, try to be as human-like as possible.
    After you have extracted the information, please summarize it in a structured way.
    """.strip()

    # Create the agent with your configured browser
    agent = Agent(
        task=TASK,
        llm=llm,
        browser=browser,
    )

    return agent

async def main():
    agent = configure_agent()

    history = await agent.run()
    print("History:", history)

if __name__ == '__main__':
    asyncio.run(main())