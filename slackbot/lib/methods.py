from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from langchain_community.document_loaders import ConfluenceLoader
import openai
from  langchain.schema import Document
import requests
import pandas as pd

def get_cosmosdb_details(subscription_id, resource_group_name):

    """
    Retrieves the URL and key for an Azure Cosmos DB account using only subscription ID and resource group name.
    Assumes resource group is limited to infrastructure provisioned in repo ARM template. 

    Args:
    subscription_id: Subscription ID of Azure Account
    resource_group_name: Name of Azure Resource Group used for infrastructure
    """

    credential = DefaultAzureCredential()
    client = CosmosDBManagementClient(credential, subscription_id)
    
    # List all Cosmos DB accounts in the resource group
    accounts = list(client.database_accounts.list_by_resource_group(resource_group_name))
    
    if not accounts:
        return "No Cosmos DB accounts found in the specified resource group."
    
    # Select the first account found
    account = accounts[0]
    endpoint = account.document_endpoint
    
    # List keys
    keys = client.database_accounts.list_read_only_keys(resource_group_name, account.name)
    primary_key = keys.primary_readonly_master_key
    
    return endpoint, primary_key

def get_subscription_and_resource_group():

    """
    Retrieves the Subscription and Resource Group information from an Azure Virtual Machine
    metadata service
    """

    metadata_url = "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
    headers = {"Metadata": "true"}
    
    response = requests.get(metadata_url, headers=headers)
    if response.status_code == 200:
        metadata = response.json()
        subscription_id = metadata["compute"]["subscriptionId"]
        resource_group = metadata["compute"]["resourceGroupName"]
        return subscription_id, resource_group
    else:
        return "Failed to retrieve subscription ID and resource group."

def get_cognitive_services_details(subscription_id, resource_group):

    """
    Retrieves Azure Cognitive Services details using an Azure Virtual Machine default credentials.
    Assumes resource group is limited to infrastructure provisioned in repo ARM template. 

    Args:
    subscription_id: Subscription ID of Azure Account
    resource_group_name: Name of Azure Resource Group used for infrastructure
    """

    credential = DefaultAzureCredential()
    client = CognitiveServicesManagementClient(credential, subscription_id)
    
    accounts = client.accounts.list_by_resource_group(resource_group)
    for account in accounts:
        key_list = client.accounts.list_keys(resource_group, account.name)
        return account.properties.endpoint, key_list.key1  # Return the first found endpoint and key
    
    return "No Cognitive Services endpoint found in the specified resource group."

def get_keyvault_url(subscription_id, resource_group_name):

    """
    Retrieves Azure Keyvault details using an Azure Virtual Machine default credentials.
    Assumes resource group is limited to infrastructure provisioned in repo ARM template. 

    Args:
    subscription_id: Subscription ID of Azure Account
    resource_group_name: Name of Azure Resource Group used for infrastructure
    """

    # Authenticate using DefaultAzureCredential
    credential = DefaultAzureCredential()
    kv_client = KeyVaultManagementClient(credential, subscription_id)
    
    # List Key Vaults in the resource group
    key_vaults = kv_client.vaults.list_by_resource_group(resource_group_name)
    
    for vault in key_vaults:
        return vault.properties.vault_uri  # Return the first Key Vault URL found
    
    return "No Key Vault found in the specified resource group."

def retrieve_secret(secret_name, vault_url):
    """
    Retrieve a secret for Azure Keyvault. Azure execution environment
    must have access to Azure Keyvault through a role assignment.

    Args:
    secret_name (str): Name of Keyvault secret to retrieve
    vault_url (strl): URI of Azure Keyvault
    """
    # Authenticate using DefaultAzureCredential
    credential = DefaultAzureCredential()

    # Create a SecretClient to interact with the Key Vault
    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    try:
        # Retrieve the secret from Key Vault
        secret = secret_client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        print(f"Error retrieving secret: {e}")

def confluence_scraper(url, token, space_key):
    loader = ConfluenceLoader(
        url=url,
        token=token
    )
    return loader.load(space_key=space_key, limit=2)

def cosmos_search(query, azure_ai_endpoint, azure_ai_api_key, vector_container):
    """
    Perform a vector search against a CosmosDB containern based on the user query.

    Args:
    query (str): The user's query string.
    azure_ai_endpoint (string): URI for Azure OpenAI embedding model deployment.
    azure_ai_api_key (string): API Key for Azure OpenAI embedding model usage 
    Returns:
    list: A list of matching documents.
    """
    #Query OpenAI Embedding endpoint. Return a vector representation of users questions
    query_embedding = get_openai_embedding(query, azure_ai_endpoint, azure_ai_api_key)
    if query_embedding is None:
        return "Invalid query or embedding generation failed"
    
    # Query CosmosDB for items with  returned embedding
    array = []
    for item in vector_container.query_items( 
        query='SELECT TOP 10 c.title, c.content, VectorDistance(c.embedding,@embedding) AS SimilarityScore FROM c ORDER BY VectorDistance(c.embedding,@embedding)', 
         parameters=[ 
            {"name": "@embedding", "value": query_embedding} 
                ], 
            enable_cross_partition_query=True): 
        array.append(item)
    return array

def DocumentsToDataframe(documents):
    """
    Transforms a Langchain Documents object in to a Pandas dataframe

    Args:
    documents: Langchain Documents object
    """
    data = []
    for doc in documents:
        row = doc.metadata
        row['page_content'] = doc.page_content
        data.append(row)
    return pd.DataFrame(data)

def get_openai_embedding(text, endpoint, token_provider):
    """
    Retrieve vector representation of text from an Azure OpenAI endpoint

    Args:
    text (string): Text that will be passed to embedding endpoint
    endpoint (string): URI for Azure OpenAI vector embedding endpoint
    api_key (string): API Key for Azure OpenAI embedding model usage 
    """
    #Establish an Azure OpenAI client
    client = openai.AzureOpenAI(
        azure_endpoint = endpoint,
        azure_ad_token_provider = token_provider,
        api_version = '2024-02-01'
    )

    #Request and return vector representation of text.
    try:

        response = client.embeddings.create(
            input=text,
            model='text-embedding-3-large',
            dimensions=768
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error fetching embedding: {e}")
        return None
    
def reencode_strings(documents):
    """
    Used to reencode strings with unknown encoding

    Args:
    documents: Langchain Documents object
    """
    for doc in documents:
        data = doc.page_content
        doc.page_content = data.encode('ascii','ignore').decode("ascii")
    return documents