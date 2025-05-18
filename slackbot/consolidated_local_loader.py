from lib.methods import *
import configparser
from azure.cosmos import CosmosClient

#This script scrapes the wiki for up to date information to prevent and saves a file locally
#Wiki is using port 80

#Establish configparser class for importing configs
config = configparser.ConfigParser()

#Import configs
config.read('config.ini')
url = config.get('DATA_LOC', 'url')
token = config.get('SECRETS', 'token')
space_key = config.get('DATA_LOC', 'space_key')
content_directory = config.get('DATA_LOC', 'content_directory')
cosmos_url = config.get('SECRETS', 'cosmos_url')
cosmos_key = config.get('SECRETS', 'cosmos_key')
cosmos_db_name = config.get('DATA_LOC', 'cosmos_db_name')
cosmos_container_name = config.get('DATA_LOC', 'cosmos_container_name')

chunk_length = 768

cosmos_client = CosmosClient(cosmos_url, credential=cosmos_key)
database = cosmos_client.get_database_client(cosmos_db_name)
container = database.get_container_client(cosmos_container_name)


#Scrape data from makersmiths wiki
documents = confluence_scraper(url, token, space_key)

#Reencode strings to clean up non-utf8 characters
documents = reencode_strings(documents)

for i, document in enumerate(documents):
    f = open("./data/data_%i.txt" %i, 'w')
    f.write(document.page_content)
    f.close()

# #Export documents to json
# save_docs_to_jsonl(documents,'./data/data.jsonl')

# #Import data from file
langchain_data = load_docs_from_jsonl(content_directory)


# #Langchain to DF
df = DocumentsToDataframe(langchain_data)

df['page_content'].str.lower()

# Adding page title to page_content

df['page_content'] = 'Content Title: ' + df['title'] + ' Content: ' +  df['page_content']

df['page_content'] = df['page_content'].apply(lambda x: str(x))

df['content_split'] = df['page_content'].apply(lambda x: [x[i:i+chunk_length] for i in range(0, len(x), chunk_length)])

exploded_df = df.explode('content_split').reset_index(drop=True)
exploded_df = exploded_df[exploded_df['content_split'].notna()]

#Smaller slice of dataset to support dev on laptop
mini_df = df[:7]

exploded_df.dropna(inplace=True)
exploded_df.reset_index(drop=True, inplace=True)
