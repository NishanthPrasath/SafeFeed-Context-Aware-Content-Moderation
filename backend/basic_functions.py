from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import snowflake.connector
import os
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI


def connect_snowflake():
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

    return conn, table_name



def disconnect_snowflake(cur, conn):
    cur.close()
    conn.close()



def scrape_reddit_policies():
    url = "https://www.redditinc.com/policies/content-policy"
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.get(url, headers=headers)
    href_dict = {}
    content_dict = {}

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.find('div', id='content')
        
        if content_div:
            links = content_div.find_all('a')
            for link in links:
                if link.text and link.get('href'):
                    href_dict[link.text.strip()] = link.get('href').strip()
        
        # IDs of divs containing the main content based on your provided HTML structure
        content_ids = ['content']

        formatted_content = ""  # Initialize an empty string to accumulate content
        
        for content_id in content_ids:

            content_div = soup.find('div', id=content_id)
            
            if content_div:
                for child in content_div.descendants:
                    if child.name in ['h1', 'h2', 'h3']:
                        formatted_content += child.text # Add headings
                    elif child.name == 'p':
                        formatted_content += child.text # Add paragraphs
                    elif child.name == 'li':
                        formatted_content += child.text # Add list items
                
                content_dict['home'] = formatted_content

            else:
                print(f"Div with id '{content_id}' not found.")
    else:
        print(f"Failed to fetch the webpage, status code: {response.status_code}")

    for name, href in href_dict.items():
        print(f"{name}: {href}")

    for key, url in href_dict.items():
        # Initialize a Selenium WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        driver.get(url)

        time.sleep(5)

        # Extract the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find the main article body
        article_body = soup.find('div', class_='lt-article__body')

        if article_body:
            # Extract the text from the article body
            content_dict[key] = article_body.get_text(separator=' ', strip=True)
            print(f"{key}: Content extracted.")  # Output the extracted text
        else:
            content_dict[key] = "Content division not found."
            print(f"{key}: Content division not found.")

        # Sleep for 5 seconds before loading the next URL
        time.sleep(5)

        driver.quit()

    # Now content_dict contains a note for each href, keyed by the original link text
    for name, content_note in content_dict.items():
        print(f"{name}: {content_note}")

    # Specify the filename
    filename = "reddit_policies.csv"

    # Writing to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['key', 'value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for key, value in content_dict.items():
            writer.writerow({'key': key, 'value': value})

    print(f"CSV file '{filename}' created successfully.")



def upload_policies_to_snowflake():
    conn, table_name = connect_snowflake()

    # Creating a cursor object
    cur = conn.cursor()

    table_name = "REDDIT_POLICIES"
    file_path = 'reddit_policies.csv'

    try:
        # Create the Table if it doesn't exist
        create_table_query = f"""
        CREATE OR REPLACE TABLE {table_name} (
            key VARCHAR(255),
            value VARCHAR(65535)
        );
        """
        cur.execute(create_table_query)
        print("Table created successfully.")
        
        # Read data from CSV file
        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                # Insert each row into the table
                insert_query = f"""
                INSERT INTO {table_name} (key, value) VALUES (%s, %s);
                """
                cur.execute(insert_query, (row[0], row[1]))
        print("Data inserted into the table successfully.")

    except Exception as e:
        print(e)
    finally:
        disconnect_snowflake(cur, conn)


def vectorize_policies():
    conn, table_name = connect_snowflake()

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
        disconnect_snowflake(cur, conn)

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


def similarity_search(text):
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
    query_text = text
    query_vector = model.encode(query_text).tolist()

    result = index.query(
    vector=query_vector,
    top_k=6
    )

    for match in result['matches']:
        print(f"ID: {match['id']}, Score: {match['score']}")

    # Pinecone query results (assuming this is the output from your previous code)
    match_ids = [match['id'] for match in result['matches']]

    conn, table_name = connect_snowflake()

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
            values_dict[row[0]] = row[1]  # The first column is 'key' and the second is 'value'

    except Exception as e:
        print(e)
    finally:
        disconnect_snowflake(cur, conn)

    # Printing the values dictionary
    for key, value in values_dict.items():
        print(f"Key: {key}, Value: {value}")

    return values_dict



def check_policies(text, policies):
    # Load your OpenAI API key from an environment variable
    client = OpenAI(
    api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
    )

    # Combine all policies into a single string
    policies_text = "\n".join([f"{key}: {value}" for key, value in policies.items()])
    prompt = f"""You are an AI model named SafeFeed, created to strictly analyze social media posts and determine if they violate a given platform's policies.
    
Platform Policies:
{policies_text}

Post Title and Text: "{text}"

Your responses should follow this format:

Policy Violation: [True/False]
Reason: [Detailed explanation if the post violates the policies, otherwise leave blank]

Strictly respond with either "True" or "False" to indicate if the post violates the platform's policies. If "True", provide a detailed "Reason" explaining how the post violates the policies. If "False", leave the "Reason" field blank.

Remember to be concise and objective in your analysis, focusing solely on whether the post adheres to or violates the platform's policies.
"""   

    response = client.completions.create(
    model="gpt-3.5-turbo-instruct",
    prompt=prompt,
    temperature=1,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    
    print(response)

    generated_response = response.choices[0].text

    return (generated_response)