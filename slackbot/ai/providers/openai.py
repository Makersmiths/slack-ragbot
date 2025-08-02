import openai
from .base_provider import BaseAPIProvider
import logging
import os
from lib.methods import *
from azure.cosmos import CosmosClient

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class OpenAI_API(BaseAPIProvider):
    MODELS = {
        "gpt-4o-mini": {"name": "GPT-4o mini", "provider": "OpenAI", "max_tokens": 16384},
    }

    def __init__(self):
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        cosmos_client = CosmosClient(os.environ.get('COSMOS_URI'), credential=os.environ.get("COSMOS_KEY"))
        database = cosmos_client.get_database_client(os.environ.get('COSMOS_DB_NAME')) #app configuration
        self.container = database.get_container_client(os.environ.get('COSMOS_CONTAINER_NAME')) #app configuration

    def set_model(self, model_name: str):
        if model_name not in self.MODELS.keys():
            raise ValueError("Invalid model")
        self.current_model = model_name

    def get_models(self) -> dict:
        if self.api_key is not None:
            return self.MODELS
        else:
            return {}
        
    def generate_response(self, prompt: str, system_content: str) -> str:
        try:
            embedding_uri = os.environ.get('OPENAI_EMBEDDING_URI')
            source_info = cosmos_search(prompt, embedding_uri, self.container)
            self.client = openai.AzureOpenAI(
                azure_endpoint = os.environ.get('OPENAI_GPT_URI'),
                api_key=self.api_key,
                api_version = '2023-05-15'
                )
            
            for x in source_info:
                system_content += "\n - Content Title: " + x['title'] + " - " + x['content'] + "\n"

            print(f"System Content: {system_content}")
            response = self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{"role": "system", "content": system_content}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except openai.APIConnectionError as e:
            logger.error(f"Server could not be reached: {e.__cause__}")
            raise e
        except openai.RateLimitError as e:
            logger.error(f"A 429 status code was received. {e}")
            raise e
        except openai.AuthenticationError as e:
            logger.error(f"There's an issue with your API key. {e}")
            raise e
        except openai.APIStatusError as e:
            logger.error(f"Another non-200-range status code was received: {e.status_code}")
            raise e
