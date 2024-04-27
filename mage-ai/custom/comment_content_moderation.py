from pandas import DataFrame
import praw
from praw.exceptions import RedditAPIException
from mage_ai.data_preparation.shared.secrets import get_secret_value

if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

reddit = praw.Reddit(
    client_id=get_secret_value('REDDIT_CLIENT_ID'),
    client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
    user_agent=get_secret_value('REDDIT_USER_AGENT'),
    username = '',
    password = ''
)

@custom
def transform_custom(data:DataFrame, *args, **kwargs):

    # Iterate over each row
    for index, row in data.iterrows():

        comment_id = row['COMMENT_ID']
        submission_id = row['SUBMISSION_ID']
        is_flagged = row['IS_FLAGGED']
        comment_author = row['COMMENT_AUTHOR']

        if is_flagged:

            try:
                # Delete the comment using PRAW
                reddit.comment(comment_id).delete()

                # Send a message to the user (comment author) notifying them of the takedown
                message_subject = "Your comment has been removed"
                message_body = f"Dear {comment_author},\n\nYour comment with ID {comment_id} has been removed by SafeFeed due to a violation of community guidelines.\n\nThank you for your understanding."
                reddit.redditor(comment_author).message(message_subject, message_body)
                                
            except RedditAPIException as e:
                # Handle any errors that occur during deletion or messaging
                print(f"An error occurred while deleting comment {comment_id}: {e}")

        data.at[index, 'DELETED'] = 'true' if is_flagged else 'false'

    return data

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
