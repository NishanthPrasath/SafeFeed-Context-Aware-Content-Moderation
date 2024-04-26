import streamlit as st
import pandas as pd

# # Function to fetch user data from Snowflake
# def fetch_user_data(conn, sf_username):

#     query = f"SELECT * FROM safefeed_users WHERE sf_username = '{sf_username}'"
#     df = pd.read_sql(query, conn)
#     return df


# Main function
def main():

    
    st.set_page_config(
        page_title="SafeFeed",
        page_icon="🤖",
    )

    # # Initialize session state
    # if 'loggedIn' not in st.session_state:
    #     st.session_state['loggedIn'] = False

    st.markdown("<h1 style='text-align: center;'>SafeFeed</h1>", unsafe_allow_html=True)
    st.title("")


# Run the app
if __name__ == '__main__':
    main()

