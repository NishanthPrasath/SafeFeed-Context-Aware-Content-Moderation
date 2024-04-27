import praw
import pandas as pd
from googleapiclient import discovery
from mage_ai.data_preparation.shared.secrets import get_secret_value
from openai import OpenAI
from gradio_client import Client
from dotenv import load_dotenv
import os
import re
import time

# Load environment variables from .env file
load_dotenv()

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

# Initialize PRAW 
API_KEY = get_secret_value('REDDIT_API_KEY')
reddit = praw.Reddit(
    client_id=get_secret_value('REDDIT_CLIENT_ID'),
    client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
    user_agent=get_secret_value('REDDIT_USER_AGENT')
)

print(get_secret_value('REDDIT_CLIENT_ID'))
print(get_secret_value('REDDIT_CLIENT_SECRET'))
print(get_secret_value('REDDIT_USER_AGENT'))

# Initialize Perspective API client
client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
)

# Initialize OpenAI client
OPENAI_API_KEY = get_secret_value('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY)

gradio_client = Client("SmilingWolf/wd-tagger")

# Function to get Perspective API scores for a text
def get_perspective_scores(text):
    analyze_request = {
        'comment': {'text': text},
        'requestedAttributes': {
            'TOXICITY': {},
            'SEVERE_TOXICITY': {},
            'IDENTITY_ATTACK': {},
            'INSULT': {},
            'PROFANITY': {},
            'THREAT': {}
        }
    }
    response = client.comments().analyze(body=analyze_request).execute()
    scores = {}
    for category, data in response['attributeScores'].items():
        scores[category] = data['summaryScore']['value']
    return scores

# Function to get OpenAI moderation categories
# def get_openai_moderation_categories(text):
#     response = openai_client.moderations.create(input=text)
#     categories = response.results[0].categories
#     return categories

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

# Function to get OpenAI moderation categories
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



@data_loader
# Data loader function
def load_data(*args, **kwargs):
    subreddit_name = kwargs.get('subreddit_name', "SafeFeed")
    posts_data = []

    # Load timestamp of the last trigger run
    last_trigger_timestamp = float(os.getenv('LAST_TRIGGER_TIMESTAMP', '0'))
    print("UTC", last_trigger_timestamp)

    for submission in reddit.subreddit(subreddit_name).new():
        # Check if the submission is newer than the last trigger run
        if submission.created_utc > last_trigger_timestamp:
        # if submission.created_utc:
            post_text = submission.title + " " + submission.selftext
            post_data = {
                'post_id': submission.id,
                'title': submission.title,
                'author': submission.author.name if submission.author else '[deleted]',
                'text': submission.selftext,
                'url': submission.url,
                **get_perspective_scores(post_text),  # Add Perspective API scores for post text
                **get_openai_moderation_categories(post_text)  # Add OpenAI moderation categories
            }
            
            # posts_data.append(post_data)
            # Check if the post contains an image URL in the text
            image_url = extract_image_url(submission.selftext)
            if image_url:
                image_tags = predict_image_tags(image_url)
                post_data['image_tags'] = image_tags
                # post_data['image_url'] = image_url
            else:
                # If no image URL found in the text, check if the post URL is an image
                if submission.url.endswith(('jpg', 'jpeg', 'png', 'gif')):
                    image_tags = predict_image_tags(submission.url)
                    post_data['image_tags'] = image_tags
                    # post_data['image_url'] = submission.url
            
            posts_data.append(post_data)

    # Update the environment variable with the current time as the new last trigger timestamp
    os.environ['LAST_TRIGGER_TIMESTAMP'] = str(time.time())

    # Create DataFrame from post data
    df_posts = pd.DataFrame(posts_data)

    return df_posts

# Test function
@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
    assert isinstance(output, pd.DataFrame), 'Output should be a DataFrame'
    print(output)  # Print the DataFrame
