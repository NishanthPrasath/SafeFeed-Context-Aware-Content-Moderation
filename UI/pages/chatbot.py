 # Importing required packages
import streamlit as st
import time
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key and assistant ID here
api_key         = os.environ['OPENAI_API_KEY']
assistant_id    = os.environ['OPENAI_ASSISTANT_ID']

client = OpenAI(
    api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
    )


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

# Set openAi client , assistant ai and assistant ai thread
@st.cache_resource
def load_openai_client_and_assistant():
    client          = OpenAI(api_key=api_key)
    my_assistant    = client.beta.assistants.retrieve(assistant_id)
    # thread          = client.beta.threads.create()

    return client , my_assistant #, thread

client,  my_assistant = load_openai_client_and_assistant()


assistant_thread = client.beta.threads.create()
my_thread = client.beta.threads.retrieve(assistant_thread.id)
# st.write(my_thread)

# check in loop  if assistant ai parse our request
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# initiate assistant ai response
def get_assistant_response(user_input=""):

    file_id = get_file_id(client=client)

    message = client.beta.threads.messages.create(
        thread_id=assistant_thread.id,
        role="user",
        content=user_input,
        file_ids=[file_id]
    )

    run = client.beta.threads.runs.create(
        thread_id=assistant_thread.id,
        assistant_id=assistant_id,
        instructions="""You are an AI assistant with access to a set of policies provided in an attached JSON file. Your task is to understand these policies thoroughly and answer users' questions based on this information. When answering, please be brief and directly address the user's query. If applicable, include a relevant chunk or key points from the policies that directly relate to the user's question. Your responses should help users understand how their inquiries relate to the specific policies without needing to read the entire document.

Please ensure your answers are:
- Direct and to the point.
- Based on the information contained in the policies.
- Include specific sections or excerpts from the policies when relevant to the user's question.
- Do not add any kind of source information like "【7†source】".

Remember, your goal is to provide informative and accurate responses that reflect the content and intent of the policies, aiding users in navigating and understanding them better."""
    )

    run = wait_on_run(run, assistant_thread)

    # Retrieve all the messages added after our last user message
    messages = client.beta.threads.messages.list(
        thread_id=assistant_thread.id, order="asc", after=message.id
    )

    # thread_messages = client.beta.threads.messages.list(assistant_thread.id)

    # st.write(thread_messages)

    return messages.data[0].content[0].text.value


if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

def submit():
    st.session_state.user_input = st.session_state.query
    st.session_state.query = ''

# Initialize or retrieve the chat history from session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    response = client.beta.threads.delete(assistant_thread.id)
    print(response)

# Function to add a new message to the chat history and update session state
def add_message(role, content):
    st.session_state.chat_history.append({'role': role, 'content': content})

# Streamlit UI
st.title(":shield: Safe-Feed policy guide :shield:")

user_input = st.text_input("Type your message:", "")

if st.button("Send"):
    if user_input:
        # Add the user message to the chat history
        add_message(role="user", content=user_input)

        # Get the assistant's response
        response = get_assistant_response(user_input)

        # Add the assistant's response to the chat history
        add_message(role="assistant", content=response)


# Display the chat history
st.header("Conversation")
for index, chat in enumerate(st.session_state.chat_history, start=1):  # start=1 to make keys more human-readable
    if chat['role'] == "user":
        # Use the message index as part of the key to ensure uniqueness
        st.text_area(label="You", value=chat['content'], key=f'user_{index}', height=100)
    else:  # Assistant's messages
        # Use the message index as part of the key to ensure uniqueness
        st.text_area(label="Assistant", value=chat['content'], key=f'assistant_{index}', height=400)
