from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.snowflake import Snowflake
from pandas import DataFrame
from os import path
from mage_ai.data_preparation.shared.secrets import get_secret_value
import snowflake.connector
import os
import time

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


Connection parameters
database = get_secret_value('SNOWFLAKE_DATABASE')
account = get_secret_value('SNOWFLAKE_ACCOUNT')
user = get_secret_value('SNOWFLAKE_USER')
password = get_secret_value('SNOWFLAKE_PASSWORD')


@data_exporter
def export_data_to_snowflake(df_posts: DataFrame, **kwargs) -> None:
    conn = None  # Initialize the connection variable
    try:
        # Establishing connection
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            database=database
        )
        print("Connection successful!")

        # Define the schema and table name
        schema = 'REDDIT'
        table_name = 'REDDIT_POSTS'
        # Create a cursor object
        cur = conn.cursor()

        # SQL command to create the schema if it doesn't exist
        create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
        cur.execute(create_schema_sql)
        print(f"Schema '{schema}' is ensured to exist.")

        # SQL command to create the table if it doesn't exist
        # You need to define the table structure according to your DataFrame's structure
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
            id VARCHAR PRIMARY KEY,
            author VARCHAR,
            body TEXT,
            parent_author VARCHAR,
            thread_id VARCHAR
            -- Add more columns as needed based on your DataFrame structure
        );
        """
        cur.execute(create_table_sql)
        print(f"Table '{table_name}' in schema '{schema}' is ensured to exist.")

        # Configuration for exporting data
        config_path = path.join(get_repo_path(), 'io_config.yaml')
        config_profile = 'default'

        # Use Snowflake loader to export data
        with Snowflake.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
            loader.export(
                df_posts,
                table_name,
                database,
                schema,
                if_exists='replace',  # Specify resolution policy if table already exists
            )
    except snowflake.connector.Error as e:
        # Error handling
        print(f"Snowflake Error: {e}")
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()
