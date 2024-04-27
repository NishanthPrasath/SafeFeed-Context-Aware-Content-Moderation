import streamlit as st
import pandas as pd
from PIL import Image


# # Function to fetch user data from Snowflake
# def fetch_user_data(conn, sf_username):

#     query = f"SELECT * FROM safefeed_users WHERE sf_username = '{sf_username}'"
#     df = pd.read_sql(query, conn)
#     return df


# Main function
def main():

    
    st.set_page_config(
        page_title="SafeFeed",
        page_icon="🛡️",
    )
    
    # Load the image
    image = Image.open('Safe_Feed_logo.jpg')
    
    # Display the image in the sidebar
    st.sidebar.image(image, caption='')

    # # Initialize session state
    # if 'loggedIn' not in st.session_state:
    #     st.session_state['loggedIn'] = False

    st.markdown("<h1 style='text-align: center;'>SafeFeed: Context-Aware Content Moderation</h1>", unsafe_allow_html=True)

    homepage_image = Image.open('Homepage_meme.jpg')

    st.image(homepage_image, caption='')

    st.title("")


# Run the app
if __name__ == '__main__':
    main()

