import streamlit as st
import praw
import time
from dotenv import load_dotenv
import os
import snowflake.connector

# Load environment variables from .env file
load_dotenv()

# Set Streamlit app title and page config
st.set_page_config(page_title="SafeFeed", page_icon=":shield:")

# Define Streamlit pages
PAGES = {
    "Login": "login",
    "Sign Up": "signup"
}

# Streamlit theme configuration
def configure_theme():
    st.markdown(
        """
        <style>
        .reportview-container {
            background: #f5f5f5;
            padding: 20px 40px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Function to check if all fields are filled
def check_fields_filled(fields):
    for field in fields:
        if not field:
            return False
    return True

def subreddit_exists(reddit, subreddit_name):
    subreddits = list(reddit.subreddits.search(subreddit_name))
    for subreddit in subreddits:
        if subreddit.display_name.lower() == subreddit_name.lower():
            return True
    return False

def email_exists(email):
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM User WHERE email = %s", (email,))
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count > 0

# Function to save user and subreddit data to Snowflake
def save_to_snowflake(email, password, full_name, subreddit_name, subreddit_description, subreddit_created_utc, subreddit_id, current_time):
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )

    cursor = conn.cursor()

    # Insert user data
    cursor.execute("""
        INSERT INTO User (email, password, full_name)
        VALUES (%s, %s, %s)
    """, (email, password, full_name))

    # Retrieve the user_id using the provided email
    cursor.execute("""
        SELECT user_id FROM User WHERE email = %s   
    """, (email,))
    user_id = cursor.fetchone()[0]

    # Insert subreddit data
    cursor.execute("""
        INSERT INTO Subreddit (subreddit_id, user_id, subreddit_name, subreddit_description, subreddit_created_utc, LAST_TRIGGER_TIMESTAMP)
        VALUES (%s, %s, %s, %s, TO_TIMESTAMP(%s), TO_TIMESTAMP(%s))
    """, (subreddit_id, user_id, subreddit_name, subreddit_description, subreddit_created_utc, current_time))

    cursor.close()
    conn.close()

# Login page content
def login():
    st.title("SafeFeed: Context Aware Moderation")
    st.write("")  # Add space
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_fields_filled([email, password]):
            # Add login functionality here
            st.success("Logged in successfully!")
        else:
            st.error("Please fill in all the fields.")

# Sign up page content
# def signup():
#     st.title("SafeFeed: Context Aware Moderation")
#     st.write("")  # Add space
#     name = st.text_input("Name")
#     email = st.text_input("Email")
#     password = st.text_input("Password", type="password")
#     subreddit_name = st.text_input("Subreddit Name")
#     reddit_username = st.text_input("Reddit Username")
#     reddit_password = st.text_input("Reddit Password", type="password")

#     if st.button("Sign Up"):
#         if check_fields_filled([name, email, password, subreddit_name, reddit_username, reddit_password]):
#             # Check if the email already exists
#             if email_exists(email):
#                 st.error("Email already exists. Please use a different email address.")
#             else:
#                 # Check if user is a moderator for the provided subreddit using PRAW
#                 reddit = praw.Reddit(
#                     client_id=os.getenv("REDDIT_CLIENT_ID"),
#                     client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
#                     user_agent=os.getenv("REDDIT_USER_AGENT"),
#                     username=reddit_username,
#                     password=reddit_password
#                 )
#                 try:
#                     subreddit = reddit.subreddit(subreddit_name)
#                     if subreddit.user_is_moderator:
#                         st.success("Sign up successful! You are a moderator of the provided subreddit.")
#                         # Get the subreddit ID
#                         subreddit_id = subreddit.id
#                         # Save user and subreddit data to Snowflake
#                         save_to_snowflake(email, password, name, subreddit_name, reddit_username, reddit_password, subreddit_id)
#                     else:
#                         st.error("You are not a moderator of the provided subreddit.")
#                 except Exception as e:
#                     st.error("An error occurred: {}".format(str(e)))
#         else:
#             st.error("Please fill in all the fields.")

def signup():
    st.title("SafeFeed: Context Aware Moderation")
    st.write("")  # Add space
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    subreddit_name = st.text_input("Subreddit Name")

    if st.button("Sign Up"):
        if check_fields_filled([name, email, password, subreddit_name]):
            # Check if the email already exists
            if email_exists(email):
                st.error("Email already exists. Please use a different email address.")
            else:
                # Validate the provided subreddit name
                reddit = praw.Reddit(
                    client_id=os.getenv("REDDIT_CLIENT_ID"),
                    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                    user_agent=os.getenv("REDDIT_USER_AGENT"),
                    username=os.getenv("REDDIT_USERNAME"),
                    password=os.getenv("REDDIT_PASSWORD")
                )
                if subreddit_exists(reddit, subreddit_name):
                    try:
                        subreddit = reddit.subreddit(subreddit_name)
                        if subreddit.user_is_moderator:
                            st.success("Sign up successful! We are already a moderator of the subreddit.")
                            subreddit_created_utc = subreddit.created_utc
                            subreddit_description = subreddit.description
                            current_time = time.time()
                            # st.write(subreddit_created_utc)
                            # st.write(subreddit_description)
                            # Save user and subreddit data to Snowflake
                            save_to_snowflake(email, password, name, subreddit_name, subreddit_description, subreddit_created_utc, subreddit.id, current_time)
                        else:
                            try:
                                subreddit.mod.accept_invite()
                                st.success("Sign up successful! We are now a moderator of the subreddit.")
                                subreddit_created_utc = subreddit.created_utc
                                subreddit_description = subreddit.description
                                current_time = time.time()
                                # Save user and subreddit data to Snowflake
                                save_to_snowflake(email, password, name, subreddit_name, subreddit_description, subreddit_created_utc, subreddit.id, current_time)
                            except praw.exceptions.RedditAPIException as e:
                                # Prompt the user to invite 'safefeedai' as a moderator
                                if "NO_INVITE_FOUND" in str(e):
                                    st.error("We are not a moderator of the subreddit yet. Please invite 'safefeedai' as a moderator through the subreddit user management page.")
                                else:
                                    st.error("An error occurred: {}".format(str(e)))   
                    except Exception as e:
                      st.error("An error occurred: {}".format(str(e)))
                else:
                    st.error("The provided subreddit does not exist. Please provide a valid subreddit name.")
        else:
            st.error("Please fill in all the fields.")

# Main function to run the Streamlit app
def main():
    configure_theme()
    st.sidebar.title("Pages")  # Change "Navigation" to "Menu"
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]
    if page == "login":
        login()
    elif page == "signup":
        signup()

if __name__ == "__main__":
    main()
