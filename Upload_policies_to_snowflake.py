import csv
import snowflake.connector
import os

# Connection parameters
account = os.getenv("SNOWFLAKE_ACCOUNT")
user = os.getenv("SNOWFLAKE_USER")
password = os.getenv("SNOWFLAKE_PASSWORD")
database = os.getenv("SNOWFLAKE_DATABASE")
schema = os.getenv("SNOWFLAKE_SCHEMA")
table_name = "REDDIT_POLICIES"
file_path = 'reddit_policies.csv'  # Update this to the path of your CSV file

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
    cur.close()
    conn.close()