import io
import pandas as pd
import requests
import praw

API_KEY = get_secret_value('REDDIT_API_KEY')
reddit = praw.Reddit(
    client_id=get_secret_value('REDDIT_CLIENT_ID'),
    client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
    user_agent=get_secret_value('REDDIT_USER_AGENT')
)

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_api(*args, **kwargs):
    subreddit_name = 'google'
    post_url = 'https://www.reddit.com/r/google/comments/1am8wnr'
    submission = reddit.submission(url=post_url)  # Get the submission object

    # Make sure to replace 'more' comments with their actual content
    submission.comments.replace_more(limit=None)
    comments_list = submission.comments.list()

    data = []
    for comment in comments_list:
        # Extract the parent comment or post author if this comment is a reply
        parent_author = None
        if not comment.is_root:  # Check if the comment is not a top-level comment
            parent_comment = comment.parent()  # Get the parent comment or submission
            if isinstance(parent_comment, praw.models.Comment):  # Check if the parent is a comment
                parent_author = parent_comment.author.name if parent_comment.author else "deleted"
            else:
                parent_author = parent_comment.author.name if parent_comment.author else "deleted"  # For top-level comments, parent is the submission itself

        comment_data = {
            'thread_id': submission.id,  # Add the submission (thread) ID
            'author': comment.author.name if comment.author else "deleted",
            'body': comment.body,
            'parent_author': parent_author,  # Add the parent author to the data dictionary
            # Add any other attributes of the comment you're interested in
        }
        data.append(comment_data)

    df = pd.DataFrame(data)

    # # Iterate over top-level comments in the submission
    # for top_level_comment in submission.comments:
    #     print_comment_details(top_level_comment)

    return df

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
    print(output)  # Print the first few rows of the DataFrame

    



def print_comment_details(comment, depth=0, parent_author=None):
    prefix = '    ' * depth
    if parent_author:
        print(f"{prefix}Reply by {comment.author} to {parent_author}: {comment.body}")
    else:
        print(f"{prefix}Comment by {comment.author}: {comment.body}")

    for reply in comment.replies:
        print_comment_details(reply, depth + 1, comment.author.name if comment.author else "deleted")


def scrape_subreddit(subreddit_name, post_url, **kwargs):

    submission = reddit.submission(url=post_url)

    # Basic details about the post
    print(f"Title: {submission.title}")
    print(f"Author: {submission.author}")
    print(f"Score: {submission.score}")
    print(f"URL: {submission.url}")

    if 'i.redd.it' in submission.url:
        print(f"Image URL: {submission.url}")

    submission.comments.replace_more(limit=None)

    return (submission.comments.list())

    # Iterates through all comments and their replies
    # for comment in submission.comments.list():
    #     print_comment_details(comment)

# Function to print comment details
def print_comment_details(comment, depth=0):
    prefix = '    ' * depth  # Indent replies for readability
    print(f"{prefix}- {comment.author}: {comment.body[:30]}...")  # Print author and a snippet of the comment

    # Iterate over and print the replies to the comment
    for reply in comment.replies:
        print_comment_details(reply, depth + 1)


