import os
import logging
from lib.methods import retrieve_secret, get_subscription_and_resource_group, get_keyvault_url, get_cognitive_services_details, get_cosmosdb_details
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from listeners import register_listeners

#Capture Azure environment context
results = get_subscription_and_resource_group()
subscription_id = results[0]
resource_group = results[1]
keyvault_url = get_keyvault_url(subscription_id, resource_group)
cs_details = get_cognitive_services_details(subscription_id, resource_group)
cosmos_details = get_cosmosdb_details(subscription_id, resource_group)

#Set environment variables
os.environ['SLACK_BOT_TOKEN']=retrieve_secret('slack-bot-token',keyvault_url)
os.environ['SLACK_APP_TOKEN']=retrieve_secret('slack-app-token',keyvault_url)
os.environ['OPENAI_GPT_URI']="{}openai/deployments/gpt-4/chat/completions/?api-version=2025-01-01-preview".format(cs_details[0])
os.environ['OPENAI_EMBEDDING_URI']="{}openai/deployments/text_embedding/embeddings/?api-version=2023-05-15".format(cs_details[0])
os.environ['AZURE_OPENAI_API_KEY']=cs_details[1]
os.environ['COSMOS_KEY']=cosmos_details[1]
os.environ['COSMOS_URI']=cosmos_details[0]
os.environ['COSMOS_DB_NAME']='vectorDB'
os.environ['COSMOS_CONTAINER_NAME']='vectorContainer'

# Initialization
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
logging.basicConfig(level=logging.DEBUG)

# Register Listeners
register_listeners(app)

# Start Bolt app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
