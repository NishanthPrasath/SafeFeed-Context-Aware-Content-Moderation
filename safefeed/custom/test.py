import re
import string
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


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

    print(sentiment_scores)

    # Use custom threshold values if needed
    if sentiment_scores['compound'] > 0:
        return "Positive"
    elif sentiment_scores['compound'] < 0:
        return "Negative"
    else:
        return "Neutral"

@custom
def transform_custom(*args, **kwargs):
    """
    args: The output from any upstream parent blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # Specify your custom logic here
    # Test the function
    reddit_comment = "This subreddit is passable! It's not informative! 🤩"
    preprocessed_comment = preprocess_text(reddit_comment)
    print(get_sentiment(preprocessed_comment))  # Output: Positive


    return {}


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
