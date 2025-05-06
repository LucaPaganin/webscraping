import asyncio
import os
import pandas as pd
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from crawl4ai import AsyncWebCrawler, CrawlResult
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination

from dotenv import load_dotenv

load_dotenv(
    # dotenv_path=".env"
)

"""
To make work this file I had to manually edit the dependencies in the installed crawl4ai package.
I had to change the required version of pillow form ~=10.4 to >=11.0.0
This is because the crawl4ai package requires a version of pillow that is not compatible with the one required by autogen_agentchat.
"""


### --- TOOLS --- ###
def estrai_markdown(url: str, proxy: str = None) -> str:
    strategy = BFSDeepCrawlStrategy(
        max_depth=2,
        include_external=False,
        max_pages=50,
        score_threshold=0.3,
    )

    async def crawl():
        async with AsyncWebCrawler(crawl_strategy=strategy, proxy=proxy) as crawler:
            result: CrawlResult = await crawler.arun(url=url)
            return result.markdown.strip()

    return asyncio.run(crawl())


model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4o-mini",
    azure_endpoint=os.environ["AZURE_OPENAI_API_BASE"],
    model="gpt-4o-mini",
    api_version="2024-12-01-preview",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

def create_team() -> RoundRobinGroupChat:
    ### --- AGENTI --- ###

    estrattore = AssistantAgent(
        name="Estrattore",
        description="A web crawler that extracts markdown from a URL.",
        system_message="You are a web crawler that extracts markdown from a URL.",
        tools=[estrai_markdown], 
        model_client=model_client
    )
    analista = AssistantAgent(
        name="Riassuntore",
        description="Un riassuntore",
        system_message="You are a data summarizer. You receive a big markdown file and you wil have to summarize it.",
        model_client=model_client
    )

    max_msg_termination = MaxMessageTermination(max_messages=3)

    # The group chat will alternate between the writer and the critic.
    group_chat = RoundRobinGroupChat([estrattore, analista], termination_condition=max_msg_termination)

    return group_chat


async def main():
    # Create the team
    group_chat = create_team()

    # `run_stream` returns an async generator to stream the intermediate messages.
    stream = group_chat.run_stream(
        task="""
        Extract markdown from the URL https://techcommunity.microsoft.com/blog/educatordeveloperblog/building-ai-agent-applications-series---using-autogen-to-build-your-ai-agents/4052280.
        Provide then a summary of the markdown.
        The summary should be in markdown format.
        """
    )
    # `Console` is a simple UI to display the stream.
    await Console(stream)
    # Close the connection to the model client.
    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
