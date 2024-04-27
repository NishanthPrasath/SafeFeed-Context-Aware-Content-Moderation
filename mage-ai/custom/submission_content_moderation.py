from mage_ai.data_preparation.shared.secrets import get_secret_value
from praw.exceptions import RedditAPIException
import praw
from pandas import DataFrame
import os
from openai import OpenAI
import time
import json
import os
import re
import requests


if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

# Load the OpenAI API key from the environment
api_key = get_secret_value('OPENAI_API_KEY')
assistant_id = get_secret_value('OPENAI_ASSISTANT_ID')
client = OpenAI(api_key=api_key)

# reddit = praw.Reddit(
#     client_id=get_secret_value('REDDIT_CLIENT_ID'),
#     client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
#     user_agent=get_secret_value('REDDIT_USER_AGENT'),
#     username = '',
#     password = ''
# )

def get_file_id(client, subreddit_name=''):
    # List all files
    response = client.files.list()

    # Iterate through the files and print details
    # for file in response.data:
    #     print(f"ID: {file.id}, Name: {file.filename}, Purpose: {file.purpose}, Created At: {file.created_at}")

    # Initialize file_id and default_file_id
    file_id = None  
    default_file_id = None

    # Iterate through the files to find specific or default file IDs
    for file in response.data:
        if file.filename == f'reddit_policies_{subreddit_name}.json':
            file_id = file.id  # Store the file ID for subreddit-specific policy
        elif file.filename == 'reddit_policies.json':
            default_file_id = file.id  # Store the file ID for default policy

    # Output the appropriate messages based on the files found
    if file_id:
        # print(f"File ID for 'reddit_policies_{subreddit_name}.json': {file_id}")
        return file_id
    else:
        print(f"File 'reddit_policies_{subreddit_name}.json' not found.")
        if default_file_id:
            print("Loading default policy file.")
            return default_file_id
        else:
            print("No default policy file found.")
            return None

def create_thread():
    thread = client.beta.threads.create()
    return thread.id

def send_message(thread_id, user_input, selected_subreddit_name):
    file_id = get_file_id(client=client, subreddit_name=selected_subreddit_name)

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input,
        file_ids=[file_id]
    )
    return message

def analyze_content_text(thread_id, assistant_id, user_input, selected_subreddit_name):
    message = send_message(thread_id, user_input, selected_subreddit_name)
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="""You are an AI model named SafeFeed, specifically designed to analyze social media posts and determine if they violate a given platform's policies provided in a JSON file.

Your responses should follow this format:

Policy Violation: [True/False]
Reason for Violation: [Detailed explanation if the post violates the policies, otherwise mention 'No violations']
Should it be Removed: [True/False]
Are you sure about this decision: [True/False]

Strictly respond with either 'True' or 'False' to indicate if the post violates the platform's policies. If 'True', provide a detailed 'Reason for Violation' explaining how the post violates the policies. Additionally, decide if the post should be removed based on the severity and nature of the violation, indicate this with 'True' or 'False' under 'Should it be Removed', and indicate whether you are sure about this decision with 'True' or 'False' under 'Are you sure about this decision'.

Remember to be concise and objective in your analysis, focusing solely on whether the post adheres to or violates the platform's policies. Your goal is to provide clear guidance on policy violations and their implications for content moderation."""
    )
    run = wait_on_run(run, thread_id)
    return run

def analyze_content_image(thread_id, assistant_id, user_input, selected_subreddit_name):
    message = send_message(thread_id, user_input, selected_subreddit_name)
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="""You are an AI model named SafeFeed, specifically designed to analyze social media posts and associated image tags to determine if they violate a given platform's policies provided in a JSON file.

Your responses should follow this format:

Policy Violation: [True/False]
Reason for Violation: [Detailed explanation if the post violates the policies, otherwise mention 'No violations']
Is image general: [True/False]
Is image sensitive: [True/False]
Is image explicit: [True/False]
Should it be Removed: [True/False]
Are you sure about this decision: [True/False]

Strictly respond with either 'True' or 'False' to indicate if the post violates the platform's policies. If 'True', provide a detailed 'Reason for Violation' explaining how the post violates the policies. Additionally, evaluate the image associated with the post:
- Indicate whether the image is general, sensitive, or explicit with 'True' or 'False' under 'Is image general', 'Is image sensitive', 'Is image explicit'.
- Decide if the post should be removed based on the severity and nature of the violation and the content of the image, indicating this with 'True' or 'False' under 'Should it be Removed'.
- Confirm the certainty of your decision with 'True' or 'False' under 'Are you sure about this decision'.

Remember to be concise and objective in your analysis, focusing solely on whether the post and its associated image adhere to or violate the platform's policies. Your goal is to provide clear guidance on policy violations and their implications for content moderation, ensuring that your responses help in making informed moderation decisions."""
    )
    run = wait_on_run(run, thread_id)
    return run

def wait_on_run(run, thread_id):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

def get_responses(thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    responses = [msg.content[0].text.value for msg in messages.data if msg.role == "assistant"]
    return responses

# Define a function to extract values using regular expressions
import re

# Define a function to extract information from image response using regular expressions
def extract_information_image(response):

    try:
        patterns = {
            'policy_violation': r"Policy Violation: (True|False)",
            'reason_for_violation': r"Reason for Violation: ([\s\S]+?)(?=Is image general|Is image sensitive|$)",
            'is_image_general': r"Is image general: (True|False)",
            'is_image_sensitive': r"Is image sensitive: (True|False)",
            'is_image_explicit': r"Is image explicit: (True|False)",
            'should_be_removed': r"Should it be Removed: (True|False)",
            'are_you_sure': r"Are you sure about this decision: (True|False)"
        }

        results = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, response)
            if match:
                results[key] = match.group(1)
            else:
                if key == 'reason_for_violation':
                    results[key] = "No violations"
                else:
                    results[key] = ""

        return results

    except Exception as e:
        print(f"An error occurred in extract_information_image: {e}")
        return None

# Define a function to extract information from text response using regular expressions
def extract_information_text(response):

    try:
        patterns = {
            'policy_violation': r"Policy Violation: (True|False)",
            'reason_for_violation': r"Reason for Violation: ([\s\S]+?)(?=Should it be Removed|Are you sure about this decision|$)",
            'should_be_removed': r"Should it be Removed: (True|False)",
            'are_you_sure': r"Are you sure about this decision: (True|False)"
        }

        results = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, response)
            if match:
                results[key] = match.group(1)
            else:
                if key == 'reason_for_violation':
                    results[key] = "No violations"
                else:
                    results[key] = ""

        return results

    except Exception as e:
        print(f"An error occurred in extract_information_text: {e}")
        return None

@custom
def transform_custom(data:DataFrame, *args, **kwargs):

    # Iterate over each row
    # print(data)
    for index, row in data.iterrows():

        image_url = ''

        if 'IMAGE_URL' in row.index:
            image_url = row['IMAGE_URL']

        subreddit_name = row['SUBREDDIT_NAME']
        submission_id = row['SUBMISSION_ID']
        is_flagged = row['IS_FLAGGED']
        image_caption = row['IMAGE_CAPTION']
       
        if image_url:

            params = {
            'url': {image_url},
            'models': 'genai',
            'api_user': get_secret_value('SE_API_USER'),
            'api_secret': get_secret_value('SE_API_SECRET'),
            }
            r = requests.get('https://api.sightengine.com/1.0/check.json', params=params)

            output = json.loads(r.text)

            ai_generated_value = output['type']['ai_generated']

            print(ai_generated_value)

            if ai_generated_value > 0.8:

                # reddit = praw.Reddit(
                #     client_id=get_secret_value('REDDIT_CLIENT_ID'),
                #     client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
                #     user_agent=get_secret_value('REDDIT_USER_AGENT'),
                #     username = '',
                #     password = ''
                # )

                reddit = praw.Reddit(
                    client_id='',
                    client_secret='',
                    user_agent= get_secret_value('REDDIT_USER_AGENT'),
                    username = '',
                    password = ''
                )

                submission = reddit.submission(submission_id)

                try:
                    # Add a comment indicating that the submission is not flagged
                    
                    comment_body = "The image associated with this submission has been detected as AI-generated by SafeFeed."
                    comment = submission.reply(comment_body)

                    # Pin the comment to the top
                    comment.mod.distinguish(how='yes', sticky=True)
                    
                except RedditAPIException as e:
                    print(f"An error occurred while adding comment to submission {submission_id}: {e}")
                
            data.drop(['IMAGE_URL'], axis=1, inplace=True)

        # Check if the submission is flagged or contains image
        # if is_flagged:

        # if not is_flagged and not image_caption:
        #     data.at[index, 'VIOLATION'] = 'No violations'
        #     data.at[index, 'DELETED'] = False
        #     data.at[index, 'IS_IMAGE_GENERAL'] = False
        #     data.at[index, 'IS_IMAGE_SENSITIVE'] = False
        #     data.at[index, 'IS_IMAGE_EXPLICIT'] = False
        #     data.at[index, 'IS_QUESTIONABLE'] = False
        #     continue

        llm_response = ''
        tags_list = {}

        # if is_flagged or image_caption:

        #     files = list_files()
        #     file_id = files.get("reddit_policies.json", None)
        #     llm_response = ''
        #     tags_list = {}

        # if file_id:

        thread_id = create_thread()

        if image_caption:
            text_image_input = f"Title: {row['SUBMISSION_TITLE']}. Text: {row['SUBMISSION_TEXT']}. Image Tags: {image_caption}"
            run = analyze_content_image(thread_id, assistant_id, text_image_input, subreddit_name)
        else:
            text_input = f"Title: {row['SUBMISSION_TITLE']}. Text: {row['SUBMISSION_TEXT']}"
            run = analyze_content_text(thread_id, assistant_id, text_input, subreddit_name)

        responses = get_responses(thread_id)
        llm_response = responses[0] if responses else "No response received from the assistant."
        client.beta.threads.delete(thread_id)

        # Retrieve tags as a dictionary to be put into snowflake
        if image_caption:
            tags_list = extract_information_image(llm_response)
        else:
            tags_list = extract_information_text(llm_response)
            
        tags_list = tags_list or {
            'policy_violation': 'false',
            'reason_for_violation': 'No violations',
            'is_image_general': 'false',
            'is_image_sensitive': 'false',
            'is_image_explicit': 'false',
            'should_be_removed': 'false',
            'are_you_sure': 'true'
        }

        policy_violation = tags_list.get('policy_violation', 'false').lower() == 'true'
        reason_for_violation = tags_list.get('reason_for_violation', 'No violations')
        should_be_removed = tags_list.get('should_be_removed', 'false').lower() == 'true'
        are_you_sure = tags_list.get('are_you_sure', 'true').lower() == 'true'

        data.at[index, 'VIOLATION'] = reason_for_violation
        data.at[index, 'DELETED'] = policy_violation
        data.at[index, 'IS_IMAGE_GENERAL'] = tags_list.get('is_image_general', 'false').lower() == 'true'
        data.at[index, 'IS_IMAGE_SENSITIVE'] = tags_list.get('is_image_sensitive', 'false').lower() == 'true'
        data.at[index, 'IS_IMAGE_EXPLICIT'] = tags_list.get('is_image_explicit', 'false').lower() == 'true'
        data.at[index, 'IS_QUESTIONABLE'] = not are_you_sure

        # print(tags_list)

        if policy_violation or should_be_removed:

            try:


                # reddit = praw.Reddit(
                #     client_id=get_secret_value('REDDIT_CLIENT_ID'),
                #     client_secret=get_secret_value('REDDIT_CLIENT_SECRET'),
                #     user_agent=get_secret_value('REDDIT_USER_AGENT'),
                #     username = '',
                #     password = ''
                # )

                reddit = praw.Reddit(
                    client_id='',
                    client_secret='',
                    user_agent= get_secret_value('REDDIT_USER_AGENT'),
                    username = '',
                    password = ''
                )

                submission = reddit.submission(submission_id)
                submission.mod.remove(spam=False)
                
                message = f"Dear {row['SUBMISSION_AUTHOR']},\n\nYour submission has been removed by SafeFeed due to a violation of community guidelines.\n\nReason for violation: {reason_for_violation} \n\nThank you for your understanding"
                submission.mod.send_removal_message(message, title='Your post has been taken down!', type='private_exposed')

                #comment
                # message = f"Your submission will be removed by SafeFeed due to a violation of community guidelines.\n\nReason for violation: {reason_for_violation}"
                # submission.reply(message)


                # Send the modmail message
                # reddit.subreddit(subreddit_name).modmail.create(message_subject, message_body, submission_author)
                # print(f"Message sent to u/{submission_author}")
                # reddit.redditor(submission_author).message(subject=message_subject, message=message_body)

            except RedditAPIException as e:
                # Handle any errors that occur during deletion or messaging
                print(f"An error occurred while deleting submission {submission_id}: {e}")

                
        # else:
        #     data.at[index, 'VIOLATION'] = '' #Response from LLM
        #     data.at[index, 'DELETED'] = False #if questionable from response make it false
        #     data.at[index, 'IS_IMAGE_GENERAL'] = False #get it from LLM for all the image values
        #     data.at[index, 'IS_IMAGE_SENSITIVE'] = False
        #     data.at[index, 'IS_IMAGE_EXPLICIT'] = False
        #     data.at[index, 'IS_QUESTIONABLE'] = False

    # print("Final",data)
    return data

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'