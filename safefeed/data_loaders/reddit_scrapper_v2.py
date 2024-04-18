import praw
import pandas as pd
from openai import OpenAI
from gradio_client import Client
from dotenv import load_dotenv
import os
import re
import time
import datetime
import snowflake.connector
from mage_ai.data_preparation.shared.secrets import get_secret_value

# Load environment variables from .env file
load_dotenv()

# Initialize PRAW 
API_KEY = get_secret_value('REDDIT_API_KEY')
reddit = praw.Reddit(
    client_id=get_secret_value('REDDIT_CLIENT_ID'),
    client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
    user_agent=get_secret_value('REDDIT_USER_AGENT')
)

# Initialize OpenAI client
OPENAI_API_KEY = get_secret_value('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY)

gradio_client = Client("SmilingWolf/wd-tagger")

def get_openai_moderation_categories(text):
    response = openai_client.moderations.create(input=text)
    categories = response.results[0].categories
    
    # Extract relevant category information
    category_dict = {
        'harassment': categories.harassment,
        'harassment_threatening': categories.harassment_threatening,
        'hate': categories.hate,
        'hate_threatening': categories.hate_threatening,
        'self_harm': categories.self_harm,
        'self_harm_instructions': categories.self_harm_instructions,
        'self_harm_intent': categories.self_harm_intent,
        'sexual': categories.sexual,
        'sexual_minors': categories.sexual_minors,
        'violence': categories.violence,
        'violence_graphic': categories.violence_graphic,
        'flagged': response.results[0].flagged  # Add flagged attribute
    }
    return category_dict

def extract_image_url(text):
    # Regular expression pattern to match complete image URLs
    pattern = r"https?://\S+"
    match = re.search(pattern, text)
    if match:
        url = match.group()
        # Check if the URL contains any of the specified image extensions
        if any(ext in url.lower() for ext in ['jpg', 'jpeg', 'png', 'gif']):
            return url
    return None

def predict_image_tags(image_url):
    result = gradio_client.predict(image_url, "SmilingWolf/wd-swinv2-tagger-v3", 0.35, False, 0.85, False, api_name="/predict")
    tags = result[0]
    return tags

def get_data(subreddit_name, last_trigger_timestamp):
    posts_data = []
    # Convert last_trigger_timestamp to Unix timestamp
    last_trigger_timestamp = last_trigger_timestamp.timestamp()

    for submission in reddit.subreddit(subreddit_name).new():
        # Check if the submission is newer than the last trigger run
        if submission.created_utc > last_trigger_timestamp:
            post_text = submission.title + " " + submission.selftext
            post_data = {
                'post_id': submission.id,
                'title': submission.title,
                'author': submission.author.name if submission.author else '[deleted]',
                'text': submission.selftext,
                'url': submission.url,
                **get_openai_moderation_categories(post_text)  # Add OpenAI moderation categories
            }

            # Check if the post contains an image URL in the text
            image_url = extract_image_url(submission.selftext)
            if image_url:
                image_tags = predict_image_tags(image_url)
                post_data['image_tags'] = image_tags
            else:
                # If no image URL found in the text, check if the post URL is an image
                if submission.url.endswith(('jpg', 'jpeg', 'png', 'gif')):
                    image_tags = predict_image_tags(submission.url)
                    post_data['image_tags'] = image_tags

            posts_data.append(post_data)

    return pd.DataFrame(posts_data)

def update_last_trigger_timestamp(conn, subreddit_name):
    cursor = conn.cursor()
    current_time = time.time()
    cursor.execute("""
        UPDATE SAFE_FEED.REDDIT.SUBREDDIT 
        SET LAST_TRIGGER_TIMESTAMP = TO_TIMESTAMP(%s)
        WHERE SUBREDDIT_NAME = %s
    """, (current_time, subreddit_name))
    conn.commit()

@data_loader
def load_data(*args, **kwargs):
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        database = 'SAFE_FEED',
        account = 'SUB15565.us-east-1',
        user = 'nishanth',
        password = 'nishTools24$',
        schema='REDDIT'
    )

    # Fetch subreddit names and last trigger timestamps from Snowflake
    cursor = conn.cursor()
    cursor.execute("SELECT SUBREDDIT_NAME, LAST_TRIGGER_TIMESTAMP FROM REDDIT.SUBREDDIT")
    subreddits = cursor.fetchall()

    # Loop through each subreddit
    for subreddit_name, last_trigger_timestamp in subreddits:
        # Call load_data() function with the subreddit name and last trigger timestamp
        df_posts = get_data(subreddit_name=subreddit_name, last_trigger_timestamp=last_trigger_timestamp)
        
        # Update LAST_TRIGGER_TIMESTAMP in Snowflake
        update_last_trigger_timestamp(conn, subreddit_name)

    # Close connection
    conn.close()

    return df_posts


# Test function
@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
    assert isinstance(output, pd.DataFrame), 'Output should be a DataFrame'
    print(output)  # Print the DataFrame
