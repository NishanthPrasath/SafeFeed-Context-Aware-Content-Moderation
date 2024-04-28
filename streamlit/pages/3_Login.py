import streamlit as st
import snowflake.connector

import os
from dotenv import load_dotenv
from PIL import Image

# Load the image
image = Image.open('Safe_Feed_logo.jpg')

# Display the image in the sidebar
st.sidebar.image(image, caption='')

# Load environment variables from .env file
load_dotenv()

# Function to establish connection to Snowflake
def connect_to_snowflake():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USERNAME"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        # warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )
    return conn


if 'user_id' not in st.session_state:
    st.session_state['user_id'] = ''

if 'email' not in st.session_state:
    st.session_state['email'] = ''

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'subreddit_array' not in st.session_state:
    st.session_state['subreddit_array'] = []

# if 'disable_logout' not in st.session_state:
#     st.session_state['disable_logout'] = True


def login():
    st.title('Login')
    email = st.text_input(label= 'email')
    password = st.text_input(label = 'Password', type='password')

    if st.button('Login'):
        conn = connect_to_snowflake()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
        result = cursor.fetchone()

        if result:
            cursor.execute("SELECT full_name FROM user WHERE email = %s", (email,))
            full_name = cursor.fetchone()[0]
            st.success(f'Welcome back {full_name}!')
            cursor.execute("SELECT user_id FROM user WHERE email = %s", (email,))
            user_id = cursor.fetchone()[0] 
            st.session_state['user_id'] = user_id
            st.session_state['email'] = email
            st.session_state['logged_in'] = True

            # Query to retrieve subreddit IDs associated with the given user ID
            subreddit_query = '''
                        SELECT subreddit_name
                        FROM subreddit
                        WHERE user_id = %s
                        '''
            cursor = conn.cursor()
            cursor.execute(subreddit_query, (st.session_state.user_id,))

            subreddit_array = [row[0] for row in cursor.fetchall()]
            st.session_state['subreddit_array'] = subreddit_array
        else:
            st.error("Email and password does not match")

# def add_subreddit(user_id):

#     st.subheader("Create a new subreddit to your account:")
#     new_subreddit_name = st.text_input("Subreddit Name:")


#     if st.button("Add Subreddit"):
#         conn = connect_to_snowflake()
#         cursor = conn.cursor()
        
#         # Insert the subreddit into the database
#         cursor.execute("INSERT INTO subreddit (SUBREDDIT_ID, USER_ID, SUBREDDIT_NAME, SUBREDDIT_DESCRIPTION, SUBREDDIT_CREATED_UTC, LAST_TRIGGER_TIMESTAMP) VALUES (%s, %s, %s, %s, %s, %s)", (te, user_id, new_subreddit_name))
#         conn.commit()
#         st.success(f'Subreddit "{new_subreddit_name}" added successfully!')

def main():
    login()

    if st.session_state.get('logged_in'):
        st.title("")

        if st.button('Logout'):
            st.success('Logged out successfully!')
            st.session_state['user_id'] = ''
            st.session_state['email'] = ''
            st.session_state['logged_in'] = False
        
        st.title("")
        st.title("")
        # add_subreddit(st.session_state.user_id)


if __name__ == '__main__':
    main()
