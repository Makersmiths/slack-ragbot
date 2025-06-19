import os
from slackbot.lib.methods import get_openai_embedding, DocumentsToDataframe, confluence_scraper, get_subscription_and_resource_group, get_keyvault_url, get_cognitive_services_details, get_cosmosdb_details, reencode_strings, retrieve_secret
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from ai.providers import get_provider_response

#Capture Azure environment context
results = get_subscription_and_resource_group()
subscription_id = results[0]
resource_group = results[1]
keyvault_url = get_keyvault_url(subscription_id, resource_group)
cs_details = get_cognitive_services_details(subscription_id, resource_group)
cosmos_details = get_cosmosdb_details(subscription_id, resource_group)
# open_details = get_openai_details(subscription_id, resource_group)

#Set environment variables
os.environ['SLACK_BOT_TOKEN']=retrieve_secret('slack-bot-token',keyvault_url)
os.environ['SLACK_APP_TOKEN']=retrieve_secret('slack-app-token',keyvault_url)
os.environ['OPENAI_GPT_URI']="{}openai/deployments/gpt-4-deployment/chat/completions/?api-version=2023-05-15".format(cs_details[0])
os.environ['OPENAI_EMBEDDING_URI']="{}openai/deployments/text-embedding-3-large/embeddings/?api-version=2023-05-15".format(cs_details[0])
os.environ['AZURE_OPENAI_API_KEY']=cs_details[1]
os.environ['COSMOS_KEY']=cosmos_details[1]
os.environ['COSMOS_URI']=cosmos_details[0]
os.environ['COSMOS_DB_NAME']='vectorDB'
os.environ['COSMOS_CONTAINER_NAME']='vectorContainer'

