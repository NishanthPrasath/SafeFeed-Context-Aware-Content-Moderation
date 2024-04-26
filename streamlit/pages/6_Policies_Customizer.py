import streamlit as st
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

def openai_connection():
    client = OpenAI(
                    api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
                    )
    
    return client

def initialize_default_policies_and_folders():
    client = openai_connection()

    # List all files
    response = client.files.list()

    # # Iterate through the files and print details
    # for file in response.data:
    #     print(f"ID: {file.id}, Name: {file.filename}, Purpose: {file.purpose}, Created At: {file.created_at}")

    # Initialize file_id and default_file_id
    file_id = None  

    # Iterate through the files to find specific or default file IDs
    for file in response.data:
        if file.filename == 'reddit_policies.json':
            file_id = file.id  # Store the file ID for default policy

    if file_id:
        return None
    else:
        # Upload the new file
        client.files.create(
            file=open('pages/Custom_policies/reddit_policies.json', "rb"),
            purpose="assistants"
            )
    
    if not os.path.exists('Custom_policies'):
        os.makedirs('Custom_policies')
        print(f"Directory 'Custom_policies' was not found and has been created.")
    else:
        print(f"Directory 'Custom_policies' already exists.")
   
def get_file_id(client, subreddit_name):
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

def update_file_openai(client, file_id, new_file_path):
    # Delete the file if it already exists
    if file_id is not None:
        client.files.delete(file_id)

    # Upload the new file
    client.files.create(
        file=open(new_file_path, "rb"),
        purpose="assistants"
        )

def load_policies(subreddit_name=None):
    """ Load policies from a JSON file. 
        Tries to load subreddit-specific policies if a subreddit name is provided,
        otherwise, loads the default policies.
    """

    if subreddit_name:
        # Construct the filename for subreddit-specific policies
        # path = f'Custom_policies/reddit_policies_{subreddit_name}.json'
        path = f'pages/Custom_policies/{subreddit_name}'
    else:
        # Default file path
        path = 'pages/Custom_policies/reddit_policies.json'   

    # Check if the specific file exists, if not, revert to the default
    if not os.path.exists(path):
        if subreddit_name != '':
            if subreddit_name and subreddit_name not in ["reddit_policies_Default policies.json"]:
                st.warning(f"No specific policy file found for subreddit '{subreddit_name}'. Loading default policies.")
        path = 'pages/Custom_policies/reddit_policies.json'

    # Try to load the file
    if os.path.exists(path):
        with open(path, 'r') as file:
            return json.load(file)
    else:
        st.error("Policy file does not exist.")
        return None

def save_policies(data, path):
    """ Save policies to a JSON file. """
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)
    st.success(f"Updated JSON file saved successfully at {path}")

initialize_default_policies_and_folders()

def main():
    st.title("Reddit Policies Customizer")
    st.write("This tool allows you to edit existing policies or create custom policy files for a specific subreddit.")

    # Input for subreddit name
    # subreddit_name = st.text_input("Enter the subreddit name to load specific policies, or leave empty for default policies:")

    subreddit_array = st.session_state.subreddit_array

    if "Default policies" not in subreddit_array:
        subreddit_array.insert(0, "Default policies")

    if subreddit_array:
        
        # Display a select box for choosing the subreddit
        st.subheader("Select your Subreddit: ")
        subreddit_name = st.selectbox("Subreddit list", subreddit_array)

    else:
        # Display a select box for choosing the subreddit
        st.subheader("Select your Subreddit: ")
        subreddit_name = st.selectbox("Subreddit list", [])

    # Using session state to store and retrieve the data and selected policy
    if 'data' not in st.session_state or st.button("Fetch policies"):
        st.session_state.data = load_policies(f'reddit_policies_{subreddit_name}.json' if subreddit_name else 'reddit_policies.json')
        if st.session_state.data is None:
            st.error("Failed to load any policy data.")

    if 'data' in st.session_state and st.session_state.data:

        data = st.session_state.data

        # Dropdown to select policy for editing
        policy_keys = list(data.keys()) if data else []
        selected_policy = st.selectbox("Select a policy to edit:", policy_keys)

        # Show current content of the policy and allow editing
        current_content = data.get(selected_policy, '')
        edited_content = st.text_area("Edit the selected policy:", value=current_content, height=200)

        if 'custom' not in policy_keys:
            # Input fields for adding a new custom policy
            st.write("Add a New Custom Policy:")
            custom_policy_name = st.text_input("Policy Name:", help="Enter a unique name for the new policy.")
            custom_policy_content = st.text_area("Policy Content:", help="Enter the content of the new policy.", height=200)

        # # Input for subreddit name
        # subreddit_name = st.text_input("Enter the subreddit name:", help="Type the name of the subreddit for which you want to create a custom policy file.")

        if st.button("Update and Create Custom Policy File"):
            if subreddit_name:
                # Update the selected policy with edited content
                if selected_policy:
                    data[selected_policy] = edited_content

                if 'custom' in data:
                    data['custom'] = edited_content

                else:
                    # Add the new custom policy under a 'custom' key
                    if custom_policy_name and custom_policy_content:
                        if 'custom' not in data:
                            data['custom'] = {}
                        data['custom'][custom_policy_name] = custom_policy_content

                # Save the updated policies to a new file named dynamically based on the subreddit name
                new_file_path = f'pages/Custom_policies/reddit_policies_{subreddit_name}.json'
                save_policies(data, new_file_path)

                # Connect with Openai
                client = openai_connection()

                # Get the appropriate file_id
                file_id = get_file_id(client=client, subreddit_name=subreddit_name)

                # Update if the file already exists or create a new one
                update_file_openai(client=client, file_id=file_id, new_file_path=new_file_path)

            else:
                st.error("Please enter a subreddit name to create a custom policy file.")

if __name__ == "__main__":
    main()