import os
from slackbot.lib.methods import get_openai_embedding, DocumentsToDataframe, confluence_scraper, get_subscription_and_resource_group, get_keyvault_url, get_cognitive_services_details, get_cosmosdb_details, reencode_strings, retrieve_secret
from azure.cosmos import CosmosClient

#Set chunk and sliding window parameters 
chunk_length = 400
overlap = 125

#Capture Azure environment context
results = get_subscription_and_resource_group()
subscription_id = results[0]
resource_group = results[1]
keyvault_url = get_keyvault_url(subscription_id, resource_group)
cs_details = get_cognitive_services_details(subscription_id, resource_group)
cosmos_details = get_cosmosdb_details(subscription_id, resource_group)

#Set environment variables for scraping/loading
os.environ['OPENAI_EMBEDDING_URI'] = "{}openai/deployments/text-embedding-3-large/embeddings/?api-version=2023-05-15".format(cs_details[0])
os.environ['OPENAI_EMBEDDING_TOKEN'] = retrieve_secret('Azure-OpenAI-embedding-token', keyvault_url)
os.environ['COSMOS_WRITE_KEY'] = retrieve_secret('cosmos-write-key', keyvault_url)
os.environ['COSMOS_URI'] = cosmos_details[0]
os.environ['COSMOS_DB_NAME'] ='vectorDB'
os.environ['COSMOS_CONTAINER_NAME'] ='vectorContainer'
os.environ['CONFLUENCE_URL'] = retrieve_secret('confluence-url', keyvault_url)
os.environ['CONFLUENCE_TOKEN'] = retrieve_secret('confluence-token', keyvault_url)
os.environ['CONFLUENCE_SPACE_KEY'] = retrieve_secret('confluence-space-key', keyvault_url)

cosmos_client = CosmosClient(os.environ.get('COSMOS_URI'), credential=os.environ.get('COSMOS_WRITE_KEY'))
database = cosmos_client.get_database_client(os.environ.get('COSMOS_DB_NAME'))
container = database.get_container_client(os.environ.get('COSMOS_CONTAINER_NAME'))

#Delete current items in container
container.delete_all_items_by_partition_key("myPartitionKey")

#Scrape data from Confluence. Will not scrape files
documents = confluence_scraper(os.environ['CONFLUENCE_URL'], os.environ['CONFLUENCE_TOKEN'], os.environ['CONFLUENCE_SPACE_KEY'])

#Reencode strings to clean up non-utf8 characters
documents = reencode_strings(documents)

#Convert to dataframe for additional processing
df = DocumentsToDataframe(documents)

#Change content to lowercase
df['page_content'].str.lower()

# Adding page title to page_content to improve semantic search and llm query context
df['page_content'] = 'Content Title: ' + df['title'] + ' Content: ' +  df['page_content']

#Typecast to string
df['page_content'] = df['page_content'].apply(lambda x: str(x))

#Chunk text with appropriate sliding window
df['content_split'] = df['page_content'].apply(
    lambda x: [x[i:i+chunk_length] for i in range(0, len(x) - overlap, chunk_length - overlap)]
)

#Explode on split content and reset index
exploded_df = df.explode('content_split').reset_index(drop=True)

#Remove NA values and reset index
exploded_df = exploded_df[exploded_df['content_split'].notna()]
exploded_df.dropna(inplace=True)
exploded_df.reset_index(drop=True, inplace=True)

#Upload items to CosmosDB container
for i in range(len(exploded_df)):
    embeddings = get_openai_embedding(exploded_df['content_split'][i], os.environ.get('OPENAI_EMBEDDING_URI'), os.environ.get('OPENAI_EMBEDDING_TOKEN'))
    container.upsert_item({
            'id': 'item{0}'.format(i),
            'title': exploded_df['title'][i],
            'source': exploded_df['source'][i],
            'content': exploded_df['content_split'][i],
            'embedding': embeddings
        }
    )