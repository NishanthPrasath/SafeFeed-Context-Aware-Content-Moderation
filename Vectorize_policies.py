import snowflake.connector
import os
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# Connection parameters
account = os.getenv("SNOWFLAKE_ACCOUNT")
user = os.getenv("SNOWFLAKE_USER")
password = os.getenv("SNOWFLAKE_PASSWORD")
database = os.getenv("SNOWFLAKE_DATABASE")
schema = os.getenv("SNOWFLAKE_SCHEMA")
table_name = "REDDIT_POLICIES"

# Establishing connection
conn = snowflake.connector.connect(
    user=user,
    password=password,
    account=account,
    database=database,
    schema=schema
)

# Creating a cursor object
cur = conn.cursor()

data_dict = {}  # Dictionary to store the data

try:
    # Execute the query to retrieve all rows from the table
    cur.execute(f"SELECT * FROM {table_name}")
    
    # Fetch the results
    rows = cur.fetchall()
    
    # Assuming 'key' is unique, use it as the dictionary key
    for row in rows:
        data_dict[row[0]] = row[1]  # Assuming the first column is 'key' and the second is 'value'

except Exception as e:
    print(e)
finally:
    cur.close()
    conn.close()

# At this point, data_dict contains all the data from REDDIT_POLICIES table
for key in data_dict.keys():
    print(key)




model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

# Initialize Pinecone
api_key = os.getenv('PINECONE_API_KEY')
pinecone_env = os.getenv('PINECONE_ENV') 
pc = Pinecone(api_key=api_key)

# Set your Pinecone index name
index_name = "reddit-policies"

# Example using a correct dimension for the 'all-MiniLM-L6-v2' model
dimension = model.get_sentence_embedding_dimension()
print(dimension)

# Check if index exists, if not create one
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=model.get_sentence_embedding_dimension(),  # Assuming model is already defined
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',  # or 'gcp' based on your preference
            region=pinecone_env
        )
    )

# Connect to the index
index = pc.Index(name=index_name)

# Proceed with vectorizing and upserting vectors into Pinecone as before
for key, text_value in data_dict.items():
    vector = model.encode(text_value).tolist()
    index.upsert(vectors=[(key, vector)])
    print(f'upserted the key: {key}')

print("All text values have been vectorized and stored in Pinecone.")