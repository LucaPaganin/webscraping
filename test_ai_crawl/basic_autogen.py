from autogen_ext.auth.azure import AzureTokenProvider
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential
from autogen_core.models import UserMessage
from dotenv import load_dotenv
import os

THISDIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(THISDIR, ".env"))

# Create the token provider
# token_provider = AzureTokenProvider(
#     DefaultAzureCredential(),
#     "https://cognitiveservices.azure.com/.default",
# )

az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4o-mini",
    model="gpt-4o-mini",
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE"),
    # azure_ad_token_provider=token_provider,  # Optional if you choose key-based authentication.
    api_key=os.getenv("AZURE_OPENAI_API_KEY"), # For key-based authentication.
)


async def main():
    result = await az_model_client.create(
        [UserMessage(content="What is the capital of France?", source="user")]
    )
    print(result)
    await az_model_client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
