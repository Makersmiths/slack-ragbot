from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.keyvault.secrets import SecretClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from langchain_community.document_loaders import ConfluenceLoader
import openai
from  langchain.schema import Document
import requests
import pandas as pd

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