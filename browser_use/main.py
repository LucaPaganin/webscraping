from datetime import datetime
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from browser_use import Agent, Browser, BrowserConfig, Controller
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from models import Immobili
import json
from prompts import IMMOBILIARE_IT_PROMPT, SHORTER_PROMPRT

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
        model="gemini-2.5-flash-preview-04-17",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=10,
        # other params...
    )

    # TASK = IMMOBILIARE_IT_PROMPT.strip()
    TASK = SHORTER_PROMPRT.strip().format(
        place="Savona",
        search_type="Compra",
        max_price=250000,
    )

    controller = Controller(output_model=Immobili)

    # Create the agent with your configured browser
    agent = Agent(
        task=TASK,
        llm=llm,
        browser=browser,
        controller=controller
    )

    return agent

async def main():
    now = datetime.now()
    print(f"Starting at {now.strftime('%Y-%m-%d %H:%M:%S')}")
    agent = configure_agent()

    history = await agent.run()
    # Save the history to a file
    final_result = history.final_result()
    outfile = f"final_results_{now.strftime('%Y%m%d_%H%M%S')}"
    try:
        final_result = json.loads(final_result)
        with open(f"{outfile}.json", "w") as f:
            json.dump(final_result, f, indent=4)
            print(f"Saved to {outfile}.json")
    except json.JSONDecodeError as e:
        # Handle JSON decode error
        print(f"Error saving JSON final result: {e}, falling back to txt file.")
        # fallback to txt file
        with open(f"{outfile}.txt", "w") as f:
            f.write(str(final_result))
            print(f"Saved to {outfile}.txt instead.")

    # Print the final result
    print("Final result:")


if __name__ == '__main__':
    asyncio.run(main())