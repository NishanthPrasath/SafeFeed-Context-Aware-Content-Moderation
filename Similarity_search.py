from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import os
import snowflake.connector

# Initialize Pinecone
api_key=os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=api_key)
# Load or Initialize your model
model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

# Set your Pinecone index name
index_name = "reddit-policies"

# Connect to the index
index = pc.Index(name=index_name)

# Example text to vectorize and search
query_text = "An adult brutally beats a child"
query_vector = model.encode(query_text).tolist()

result = index.query(
  vector=query_vector,
  top_k=3
)

for match in result['matches']:
    print(f"ID: {match['id']}, Score: {match['score']}")



# Pinecone query results (assuming this is the output from your previous code)
match_ids = [match['id'] for match in result['matches']]

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

values_dict = {}  # Dictionary to store the values corresponding to the match IDs

try:
    # Formatting the match IDs for SQL query
    match_ids_str = "', '".join(match_ids)
    
    # Execute the query to retrieve values corresponding to the match IDs
    cur.execute(f"SELECT * FROM {table_name} WHERE key IN ('{match_ids_str}')")
    
    # Fetch the results
    rows = cur.fetchall()
    
    # Storing the results in the dictionary
    for row in rows:
        values_dict[row[0]] = row[1]  # Assuming the first column is 'key' and the second is 'value'

except Exception as e:
    print(e)
finally:
    cur.close()
    conn.close()

# Printing the values dictionary
for key, value in values_dict.items():
    print(f"Key: {key}, Value: {value}")


# Create a prompt saying
    # Can you tell me if the post "{Post content}" adheres to the policy "{Policy}"

 