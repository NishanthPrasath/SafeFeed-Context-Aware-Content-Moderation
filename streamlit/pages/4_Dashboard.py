import streamlit as st
import pandas as pd
import snowflake.connector
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objs as go
import seaborn as sns
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

# Function to retrieve count of submissions for a specific subreddit_id
def get_submission_count(selected_subreddit_id, conn):
    # Query to get the total number of submissions for the provided subreddit_id
    submissions_query = f'''
                        SELECT COUNT(submission_id) AS total_submissions
                        FROM submission
                        WHERE subreddit_id = '{selected_subreddit_id}'
                        '''

    # Execute query
    submissions_data = pd.read_sql(submissions_query, conn)
    submission_count = submissions_data.iloc[0]['TOTAL_SUBMISSIONS']
    return submission_count

def get_comment_count(selected_subreddit_id, conn):
    # Query to get the total number of submissions for the provided subreddit_id
    comments_query = f'''
                        SELECT COUNT(c.comment_id) AS total_comments
                        FROM submission s
                        JOIN comment c ON s.submission_id = c.submission_id
                        WHERE s.subreddit_id = '{selected_subreddit_id}'
                        '''

    # Execute query
    comments_data = pd.read_sql(comments_query, conn)
    comment_count = comments_data.iloc[0]['TOTAL_COMMENTS']
    return comment_count

# Function to retrieve count of flagged submissions for a specific subreddit_id
def get_flagged_submission_count(selected_subreddit_id, conn):
    flagged_query = f'''
                    SELECT COUNT(submission_id) AS flagged_submissions
                    FROM submission
                    WHERE subreddit_id = '{selected_subreddit_id}' AND is_flagged = 1
                    '''
    flagged_data = pd.read_sql(flagged_query, conn)
    flagged_count = flagged_data.iloc[0]['FLAGGED_SUBMISSIONS']
    return flagged_count



# Function to retrieve sentiment category counts for a specific subreddit_id
def get_sentiment_category_counts(selected_subreddit_id, conn):
    sentiment_query = f'''
                        SELECT sentiment_category, COUNT(*) AS category_count
                        FROM submission
                        WHERE subreddit_id = '{selected_subreddit_id}'
                        GROUP BY sentiment_category
                        '''
    sentiment_data = pd.read_sql(sentiment_query, conn)
    return sentiment_data

def sentiment_count(sentiment_data):
    sentiment_counts = {
        'positive': sentiment_data.loc[sentiment_data['SENTIMENT_CATEGORY'] == 'Positive', 'CATEGORY_COUNT'].iloc[0] if 'Positive' in sentiment_data['SENTIMENT_CATEGORY'].values else 0,
        'negative': sentiment_data.loc[sentiment_data['SENTIMENT_CATEGORY'] == 'Negative', 'CATEGORY_COUNT'].iloc[0] if 'Negative' in sentiment_data['SENTIMENT_CATEGORY'].values else 0,
        'neutral': sentiment_data.loc[sentiment_data['SENTIMENT_CATEGORY'] == 'Neutral', 'CATEGORY_COUNT'].iloc[0] if 'Neutral' in sentiment_data['SENTIMENT_CATEGORY'].values else 0
    }
    return sentiment_counts



def display_pie_chart(sentiment_data):
    # Define custom colors
    custom_colors = ['#50C878', '#FF6961', '#ffefd5']  

    # Capitalize the first letter of each sentiment category
    sentiment_data['SENTIMENT_CATEGORY'] = sentiment_data['SENTIMENT_CATEGORY'].str.capitalize()

    fig = px.pie(sentiment_data, 
                 values='CATEGORY_COUNT', 
                 names='SENTIMENT_CATEGORY',
                 color='SENTIMENT_CATEGORY', 
                 color_discrete_sequence=custom_colors,
                 hole=0.5
                )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title='SENTIMENT CATEGORY COUNTS', title_x=0.5, paper_bgcolor='#273346')
    st.plotly_chart(fig)

   

# Function to display a pie chart of flagged vs unflagged submissions
def display_flagged_pie_chart(flagged_count, unflagged_count):
    labels = ['Flagged Posts', 'Unflagged Posts']
    values = [flagged_count, unflagged_count]

    fig = px.pie(names=labels, values=values, hole=0.35, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title='FLAGGED vs UNFLAGGED SUBMISSIONS', title_x=0.5, paper_bgcolor='#273346')
    st.plotly_chart(fig)




def get_category_counts(selected_subreddit_id, conn):
    # Query to retrieve counts for each category
    category_query = f'''
                    SELECT
                        SUM(CASE WHEN is_text_hate_speech THEN 1 ELSE 0 END) text_hate_speech_count,
                        SUM(CASE WHEN is_text_harassment THEN 1 ELSE 0 END) AS text_harassment_count,
                        SUM(CASE WHEN is_text_self_harm THEN 1 ELSE 0 END) AS text_self_harm_count,
                        SUM(CASE WHEN is_text_sexual_content THEN 1 ELSE 0 END) AS text_sexual_content_count,
                        SUM(CASE WHEN is_text_violence THEN 1 ELSE 0 END) AS text_violence_count,
                        
                        SUM(CASE WHEN is_image_general THEN 1 ELSE 0 END) AS image_general_count,
                        SUM(CASE WHEN is_image_sensitive THEN 1 ELSE 0 END) AS image_sensitive_count,
                        SUM(CASE WHEN is_image_explicit THEN 1 ELSE 0 END) AS image_explicit_count,

                        SUM(CASE WHEN is_questionable THEN 1 ELSE 0 END) AS questionable_count

                    FROM submission
                    WHERE subreddit_id = '{selected_subreddit_id}'
                    '''

    # Execute the query
    category_data = pd.read_sql(category_query, conn)

    # Extract the category counts
    category_counts = category_data.iloc[0].tolist()

    return category_counts



def display_category_bar_chart(category_counts):
    categories = ["Hate Speech", "Harassment", "Self Harm", "Sexual Content", "Violence", "General Image", "Sensitive Image", "Explicit Image", "Questionable"]
    
    # Combine categories and counts, then sort in descending order
    sorted_data = sorted(zip(categories, category_counts), key=lambda x: x[1], reverse=False)
    sorted_categories, sorted_counts = zip(*sorted_data)
    
    fig = px.bar(y=sorted_categories, x=sorted_counts, color=sorted_categories, orientation='h', labels={'y': 'Categories', 'x': 'Counts'}, title=' ')
    fig.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.6)
    fig.update_layout(title_x=0.5, paper_bgcolor='#273346', xaxis=dict(tickvals=list(range(min(sorted_counts), max(sorted_counts)+1)), showgrid=True))
    return fig





def get_comment_count_by_sentiment(selected_subreddit_id, conn):
    # Define the SQL query
    query = f'''
        SELECT c.sentiment_category, COUNT(c.comment_id) AS comment_count
        FROM comment c
        JOIN submission s ON c.submission_id = s.submission_id
        WHERE s.subreddit_id = '{selected_subreddit_id}'
        GROUP BY c.sentiment_category
    '''

    sentiment_comment_data = pd.read_sql(query, conn)
    return sentiment_comment_data

def sentiment_comment_count(sentiment_comment_data):
    sentiment_comment_counts = {
        'positive': sentiment_comment_data.loc[sentiment_comment_data['SENTIMENT_CATEGORY'] == 'Positive', 'COMMENT_COUNT'].iloc[0] if 'Positive' in sentiment_comment_data['SENTIMENT_CATEGORY'].values else 0,
        'negative': sentiment_comment_data.loc[sentiment_comment_data['SENTIMENT_CATEGORY'] == 'Negative', 'COMMENT_COUNT'].iloc[0] if 'Negative' in sentiment_comment_data['SENTIMENT_CATEGORY'].values else 0,
        'neutral': sentiment_comment_data.loc[sentiment_comment_data['SENTIMENT_CATEGORY'] == 'Neutral', 'COMMENT_COUNT'].iloc[0] if 'Neutral' in sentiment_comment_data['SENTIMENT_CATEGORY'].values else 0
    }
    return sentiment_comment_counts

def display_pie_chart_comment(sentiment_data):
    # Define custom colors
    custom_colors = ['#50C878', '#FF6961', '#ffefd5']  

    # Capitalize the first letter of each sentiment category
    sentiment_data['SENTIMENT_CATEGORY'] = sentiment_data['SENTIMENT_CATEGORY'].str.capitalize()

    fig = px.pie(sentiment_data, 
                 values='COMMENT_COUNT', 
                 names='SENTIMENT_CATEGORY',
                 color='SENTIMENT_CATEGORY', 
                 color_discrete_sequence=custom_colors,
                 hole=0.5
                )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title='SENTIMENT COMMENT COUNTS', title_x=0.5, paper_bgcolor='#273346')
    st.plotly_chart(fig)

def get_flagged_comment_count(selected_subreddit_id, conn):
    # Define the SQL query
    query = f"""
        SELECT COUNT(comment_id) AS flagged_comment_count
        FROM comment c
        JOIN submission s ON c.submission_id = s.submission_id
        WHERE s.subreddit_id = '{selected_subreddit_id}'
        AND c.is_flagged = 1
    """

    flagged_data = pd.read_sql(query, conn)
    flagged_count = flagged_data.iloc[0]['FLAGGED_COMMENT_COUNT']
    return flagged_count


# Function to display a pie chart of flagged vs unflagged submissions
def display_flagged_comment_pie_chart(flagged_count, unflagged_count):
    labels = ['Flagged Comments', 'Unflagged Comments']
    values = [flagged_count, unflagged_count]

    fig = px.pie(names=labels, values=values, hole=0.25, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title='FLAGGED vs UNFLAGGED COMMENTS', title_x=0.5, paper_bgcolor='#273346')
    st.plotly_chart(fig)





def get_category_comment_counts(selected_subreddit_id, conn):
    # Query to retrieve counts for each category
    category_query = f'''
                    SELECT
                        SUM(CASE WHEN c.is_text_hate_speech THEN 1 ELSE 0 END) text_hate_speech_count,
                        SUM(CASE WHEN c.is_text_harassment THEN 1 ELSE 0 END) AS text_harassment_count,
                        SUM(CASE WHEN c.is_text_self_harm THEN 1 ELSE 0 END) AS text_self_harm_count,
                        SUM(CASE WHEN c.is_text_sexual_content THEN 1 ELSE 0 END) AS text_sexual_content_count,
                        SUM(CASE WHEN c.is_text_violence THEN 1 ELSE 0 END) AS text_violence_count

                    FROM comment c
                    JOIN submission s ON c.submission_id = s.submission_id
                    WHERE s.subreddit_id = '{selected_subreddit_id}'
                    '''

    # Execute the query
    category_data = pd.read_sql(category_query, conn)

    # Extract the category counts
    category_counts = category_data.iloc[0].tolist()

    return category_counts


def display_comment_category_bar_chart(category_counts):
    categories = ["Hate Speech", "Harassment", "Self Harm", "Sexual Content", "Violence", "Questionable"]
    
    # Combine categories and counts, then sort in descending order
    sorted_data = sorted(zip(categories, category_counts), key=lambda x: x[1], reverse=False)
    sorted_categories, sorted_counts = zip(*sorted_data)
    
    fig = px.bar(y=sorted_categories, x=sorted_counts, color=sorted_categories, orientation='h', labels={'y': 'Categories', 'x': 'Counts'}, title=' ')
    fig.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.6)
    fig.update_layout(title_x=0.5, paper_bgcolor='#273346', xaxis=dict(tickvals=list(range(min(sorted_counts), max(sorted_counts)+1)), showgrid=True))
    return fig


# Define function to plot submission count by hour
def plot_submission_count_by_hour(subreddit_id, selected_subreddit_name, conn):
    # Fetch data from Snowflake
    query = f"""
    SELECT 
        EXTRACT(HOUR FROM SUBMISSION_TIMESTAMP) AS HOUR,
        COUNT(SUBMISSION_ID) AS SUBMISSION_COUNT
    FROM 
        SUBMISSION
    WHERE 
        SUBREDDIT_ID = '{subreddit_id}'
    GROUP BY 
        EXTRACT(HOUR FROM SUBMISSION_TIMESTAMP)
    ORDER BY 
        EXTRACT(HOUR FROM SUBMISSION_TIMESTAMP)
    """
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(data, columns=columns)

    # Create a DataFrame with all hours of the day and set submission count to 0
    all_hours = pd.DataFrame({'HOUR': range(24)})
    df = pd.merge(all_hours, df, how='left', on='HOUR')
    df['SUBMISSION_COUNT'].fillna(0, inplace=True)
    
    # Create Plotly line graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['HOUR'], y=df['SUBMISSION_COUNT'], mode='lines+markers'))
    fig.update_layout(title=f'Submission Count by Hour for Subreddit {selected_subreddit_name}',
                      xaxis_title='Hour of the Day',
                      yaxis_title='Submission Count',
                      xaxis=dict(tickmode='array', tickvals=list(range(24)), ticktext=[str(i) for i in range(24)]),
                      yaxis=dict(tickmode='linear', tick0=0, dtick=1, range=[0, df['SUBMISSION_COUNT'].max()]),
                      xaxis_range=[0, 23])  # Set x-axis range from 0 to 23
    
    return fig




# Function to display a table with Plotly
def display_repeated_violator_table(selected_subreddit_id, conn):
    # Execute the query
    query = f"""
    SELECT 
        author_name,
        violation_count
    FROM 
        repeatedviolator
    WHERE 
        SUBREDDIT_ID = '{selected_subreddit_id}'
    ORDER BY 
        violation_count DESC
    LIMIT 5
    """
    cursor = conn.cursor()
    cursor.execute(query)

    # Fetch all rows
    rows = cursor.fetchall()


    # Get author names and violation counts
    authors = [row[0] for row in rows]
    violation_counts = [row[1] for row in rows]

    # Create Plotly vertical bar graph
    fig = go.Figure([go.Bar(
        x=authors,
        y=violation_counts,
        marker_color='skyblue',  # Color of the bars
    )])
    fig.update_layout(title='Top 5 Repeated Violators',
                      xaxis_title='Author Name',
                      yaxis_title='Violation Count',
                      xaxis_tickangle=-45,  # Rotate x-axis labels for better readability
                      yaxis=dict(tickmode='linear', tick0=0, dtick=1),  # Set y-axis step to 1
                      margin=dict(t=50, l=0, r=0, b=30))  # Adjust margins for better visibility

    # Display Plotly vertical bar graph
    st.plotly_chart(fig)


# Function to display deleted posts from Snowflake
def display_deleted_posts(subreddit_id, conn):
    # Execute the query
    query = f"""
    SELECT 
        submission_id,
        submission_title,
        submission_text,
        submission_author,
        violation
    FROM 
        submission
    WHERE 
        subreddit_id = '{subreddit_id}'
        AND deleted = TRUE
    """
    cursor = conn.cursor()
    cursor.execute(query)

    # Fetch all rows
    rows = cursor.fetchall()

    # Get column names
    columns = [desc[0] for desc in cursor.description]

    # Create DataFrame
    df = pd.DataFrame(rows, columns=columns)

    # Display DataFrame as a table
    st.dataframe(df)


# Main function
def main():


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
        
    # Establish Snowflake connection
    conn = connect_to_snowflake()

    # Streamlit app
    st.markdown("<h1 style='text-align: center;'>Dashboard</h1>", unsafe_allow_html=True)
    st.title("")

    if st.session_state['logged_in'] == False:
        st.title("Please log-in to access this feature!")

    else:

        st.title("")

        conn = connect_to_snowflake()

        cursor = conn.cursor()
        
        subreddit_array = st.session_state.subreddit_array

        if "Default policies" in subreddit_array:
            subreddit_array.remove("Default policies")

        if subreddit_array:
            
            # Display a select box for choosing the subreddit
            st.subheader("Select your Subreddit: ")
            selected_subreddit_name = st.selectbox("", subreddit_array)
            st.title("")
            st.title("")

            # Query to retrieve the corresponding subreddit ID based on the selected subreddit name
            subreddit_id_query = '''
                                SELECT subreddit_id
                                FROM subreddit
                                WHERE user_id = %s
                                AND subreddit_name = %s
                                '''

            # Execute the query
            cursor.execute(subreddit_id_query, (st.session_state.user_id, selected_subreddit_name))
            selected_subreddit_id = cursor.fetchone()[0]

            # st.write(f"Selected subreddit ID: {selected_subreddit_id}")
                


            cursor = conn.cursor()
            cursor.execute("SELECT subreddit_name FROM subreddit WHERE subreddit_id = %s", (selected_subreddit_id,))
            subreddit_name = cursor.fetchone()[0] 
            
            st.subheader(f"Subreddit : {subreddit_name}")

        
            # Display count of submissions for the provided subreddit_id

            submission_count = get_submission_count(selected_subreddit_id, conn)
            comment_count = get_comment_count(selected_subreddit_id, conn)

            # Display count of submissions with containers
            submissions_container = st.container()
            with submissions_container:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>TOTAL SUBMISSIONS<br><span style='font-size: 30px; font-weight: bold;'>{submission_count}</span></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>TOTAL COMMENTS<br><span style='font-size: 30px; font-weight: bold;'>{comment_count}</span></div>", unsafe_allow_html=True)

        
            st.title("")
            st.title("")





            # Plot submission count by hour for selected subreddit
            st.plotly_chart(plot_submission_count_by_hour(selected_subreddit_id, selected_subreddit_name, conn))


            st.title("")
            st.title("")

            # Create tabs
            tab1, tab2, tab3 = st.tabs(["SUBMISSIONS", "COMMENTS", "DELETED POSTS"])

            # Content for Tab 1
            with tab1:
                    
                sentiment_data = get_sentiment_category_counts(selected_subreddit_id, conn)

                # Get sentiment counts
                sentiment_counts = sentiment_count(sentiment_data)
                
                
                # Display sentiment counts with containers
                st.subheader("Sentiment Count:")
                sentiment_container = st.container()
            
                with sentiment_container:
                    st.markdown('<div class="header"></div>', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>POSITIVE SUBMISSIONS<br><span style='font-size: 24px; font-weight: bold;'>{sentiment_counts['positive']}</span></div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>NEGATIVE SUBMISSIONS<br><span style='font-size: 24px; font-weight: bold;'>{sentiment_counts['negative']}</span></div>", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>NEUTRAL SUBMISSIONS<br><span style='font-size: 24px; font-weight: bold;'>{sentiment_counts['neutral']}</span></div>", unsafe_allow_html=True)

                st.write("")
            
                display_pie_chart(sentiment_data)

                st.title("")
                st.title("")

                flagged_count = get_flagged_submission_count(selected_subreddit_id, conn)
                unflagged_count = submission_count-flagged_count


                # Display flagged posts with containers
                st.subheader("Flagged vs Unflagged Posts:")
                flagged_container = st.container()
                with flagged_container:
                    st.markdown('<div class="header"></div>', unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>FLAGGED SUBMISSIONS<br><span style='font-size: 24px; font-weight: bold;'>{flagged_count}</span></div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>UNFLAGGED SUBMISSIONS<br><span style='font-size: 24px; font-weight: bold;'>{unflagged_count}</span></div>", unsafe_allow_html=True)

                st.write("")
                # Display pie chart for flagged vs unflagged submissions
                display_flagged_pie_chart(flagged_count, unflagged_count)
                

                st.title("")
                st.title("")
                st.subheader("Count of submissions based on the categories: ")
                # Get counts for each category
                category_counts = get_category_counts(selected_subreddit_id, conn)


                # Display bar chart for category counts
                bar_chart_fig = display_category_bar_chart(category_counts)
                st.plotly_chart(bar_chart_fig)
            
            # Content for Tab 2
            with tab2:
                    
                sentiment_comment_data = get_comment_count_by_sentiment(selected_subreddit_id, conn)

                # Get sentiment counts
                sentiment_comment_counts = sentiment_comment_count(sentiment_comment_data)
                
                
                # Display sentiment counts with containers
                st.subheader("Sentiment Count:")
                sentiment_comment_container = st.container()
            
                with sentiment_comment_container:
                    st.markdown('<div class="header"></div>', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>POSITIVE COMMENTS<br><span style='font-size: 24px; font-weight: bold;'>{sentiment_comment_counts['positive']}</span></div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>NEGATIVE COMMENTS<br><span style='font-size: 24px; font-weight: bold;'>{sentiment_comment_counts['negative']}</span></div>", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>NEUTRAL COMMENTS<br><span style='font-size: 24px; font-weight: bold;'>{sentiment_comment_counts['neutral']}</span></div>", unsafe_allow_html=True)

                st.write("")
            
                display_pie_chart_comment(sentiment_comment_data)

                st.title("")
                st.title("")


                flagged_comment_count = get_flagged_comment_count(selected_subreddit_id, conn)
                unflagged_comment_count = comment_count-flagged_comment_count


                # Display flagged comments with containers
                st.subheader("Flagged vs Unflagged Comments:")
                flagged_comment_container = st.container()
                with flagged_comment_container:
                    st.markdown('<div class="header"></div>', unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>FLAGGED COMMENTS<br><span style='font-size: 24px; font-weight: bold;'>{flagged_comment_count}</span></div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<div style='text-align: center; padding: 20px; background-color: #273346; color: white; border-radius: 10px;'>UNFLAGGED COMMENTS<br><span style='font-size: 24px; font-weight: bold;'>{unflagged_comment_count}</span></div>", unsafe_allow_html=True)

                st.write("")
                # Display pie chart for flagged vs unflagged submissions
                display_flagged_comment_pie_chart(flagged_comment_count, unflagged_comment_count)          

                st.title("")
                st.title("")
                st.subheader("Count of comments based on the categories: ")
                # Get counts for each category
                comment_category_counts = get_category_comment_counts(selected_subreddit_id, conn)

                # Display bar chart for category counts
                comment_bar_chart_fig = display_comment_category_bar_chart(comment_category_counts)
                st.plotly_chart(comment_bar_chart_fig)
            
            with tab3:

                st.title("")
                st.subheader("Displaying Deleted Posts:")
                st.title("")
                try:
                    # Call the function to display deleted posts
                    display_deleted_posts(selected_subreddit_id, conn)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

                st.title("")
                st.subheader("Displaying Top 5 repeated violators:")
                st.title("")

                try:
                    display_repeated_violator_table(selected_subreddit_id, conn)

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            

                



        else:
            st.write("No subreddits created")

        # Close the database connection
        conn.close()


# Run the main function
if __name__ == "__main__":

        main()

