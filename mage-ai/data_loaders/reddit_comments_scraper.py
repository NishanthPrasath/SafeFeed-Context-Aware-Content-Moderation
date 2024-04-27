import pandas as pd
import praw
from googleapiclient import discovery
from openai import OpenAI
import time
import datetime
import snowflake.connector
from mage_ai.data_preparation.shared.secrets import get_secret_value
import re
import string
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

# Initialize PRAW 
reddit = praw.Reddit(
    client_id=get_secret_value('REDDIT_CLIENT_ID'),
    client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
    user_agent=get_secret_value('REDDIT_USER_AGENT')
)

# Initialize OpenAI client
OPENAI_API_KEY = get_secret_value('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY)

processed_comments = set()

# Function to get comments recursively
def get_comments(submission_id, comment, level=0, replied_to=None):
    comments_data = []
    replies = comment.replies
    for reply in replies:
        if isinstance(reply, praw.models.MoreComments):
            continue
        preprocessed_comment = preprocess_text(reply.body)
        comment_data = {
            'COMMENT_ID': reply.id,
            'SUBMISSION_ID': submission_id,
            'COMMENT_AUTHOR': reply.author.name if reply.author else '[deleted]',
            'COMMENT_TIMESTAMP': reply.created_utc,
            'COMMENT_TEXT': reply.body,
            'REPLIED_TO': replied_to,
            'LEVEL': level,
            'SENTIMENT_CATEGORY': get_sentiment(preprocessed_comment),
            **get_openai_moderation_categories(reply.body)
        }
        comments_data.append(comment_data)
        comments_data.extend(get_comments(submission_id, reply, level + 1, replied_to=reply.author.name if reply.author else '[deleted]'))
        processed_comments.add(reply.id)
    return comments_data

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
        'IS_FLAGGED': response.results[0].flagged  # Add flagged attribute
    }
    return category_dict

def replace_emojis(text):
    return emoji.demojize(text, delimiters=(" ", " "))

def preprocess_text(text):

    # Lowercase the text
    text = text.lower()
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove special characters and punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Replace emojis with their descriptions
    text = replace_emojis(text)

    return text

def get_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = analyzer.polarity_scores(text)

    # print(sentiment_scores)

    # Use custom threshold values if needed
    if sentiment_scores['compound'] > 0:
        return "Positive"
    elif sentiment_scores['compound'] < 0:
        return "Negative"
    else:
        return "Neutral"

def update_last_trigger_timestamp(conn, submission_id):
    cursor = conn.cursor()
    current_time = time.time()
    cursor.execute("""
        UPDATE SAFE_FEED.REDDIT.SUBMISSION 
        SET LAST_TRIGGER_TIMESTAMP = TO_TIMESTAMP(%s)
        WHERE SUBMISSION_ID = %s
    """, (current_time, submission_id))
    conn.commit()

@data_loader
def load_data(data: pd.DataFrame, *args, **kwargs):

    # Connect to Snowflake
    conn = snowflake.connector.connect(
        database = get_secret_value('Nishanth_SF_DB'),
        account = get_secret_value('Nishanth_SF_ACCOUNT'),
        user = get_secret_value('Nishanth_SF_User'),
        password = get_secret_value('Nishanth_SF_PSWD'),
        schema=get_secret_value('Nishanth_SF_Schema')
    )

    # Fetch subreddit names and last trigger timestamps from Snowflake
    cursor = conn.cursor()
    cursor.execute("SELECT SUBMISSION_ID, SUBREDDIT_ID, LAST_TRIGGER_TIMESTAMP FROM REDDIT.SUBMISSION")
    submissions = cursor.fetchall()

    comments_data = []

    # Loop through each subreddit
    for submission_id, subreddit_id, last_trigger in submissions:

        # Get submission object
        submission = reddit.submission(id=submission_id)
        last_trigger_timestamp = last_trigger.timestamp()
        # if not data.empty:
        #     last_trigger_timestamp = data['last_trigger'][0]
        
        # Iterate over comments in submission
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            if comment.id not in processed_comments:  # Check if comment has not been processed
                # Check if comment is newer than last trigger timestamp
                if comment.created_utc > last_trigger_timestamp:
                    preprocessed_comment = preprocess_text(comment.body)
                    comment_data = {
                        'COMMENT_ID': comment.id,
                        'SUBMISSION_ID': submission_id,
                        'COMMENT_TEXT': comment.body,
                        'COMMENT_AUTHOR': comment.author.name if comment.author else '[deleted]',
                        'COMMENT_TIMESTAMP': comment.created_utc,
                        'REPLIED_TO': submission.author.name if submission.author else '[deleted]',
                        'LEVEL': 0,
                        'SENTIMENT_CATEGORY': get_sentiment(preprocessed_comment),
                        **get_openai_moderation_categories(comment.body)
                    }
                    comments_data.append(comment_data)
                    comments_data.extend(get_comments(submission_id, comment, level=1, replied_to=comment.author.name if comment.author else '[deleted]'))
                processed_comments.add(comment.id)  # Add comment to processed set

        update_last_trigger_timestamp(conn, submission_id)
           

    # Create DataFrame from comments data
    df_comments = pd.DataFrame(comments_data)

    conn.close()

    return df_comments


    # df_all_posts = pd.concat(all_posts, ignore_index=True)

    # df_all_posts['last_trigger'] =  last_trigger_timestamp

    # # Close connection
    # conn.close()

    # return df_all_posts


@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
    assert isinstance(output, pd.DataFrame), 'Output should be a DataFrame'
    print(output)