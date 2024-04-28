# SafeFeed: Context-Aware Content Moderation with Generative AI

SafeFeed is an innovative platform that harnesses the power of Generative AI and Large Language Models (LLMs) to revolutionize content moderation on social media platforms like Reddit. It aims to create healthier online communities by ensuring that the shared content adheres to community guidelines while preserving the essence of open discussions.

## Features

- **Text Content Moderation**: SafeFeed utilizes the OpenAI Moderation API to analyze text content (posts and comments) for policy violations, such as hate speech, harassment, or threats.
- **Image Analysis**: SafeFeed employs the Waifu Diffusion model to accurately capture important details in images, aiding in understanding the context of visual content.
- **Generative AI**: SafeFeed leverages OpenAI's GPT-4 model to interpret the meaning of text and images, enabling context-aware content moderation decisions based on platform policies.
- **Policy Retrieval**: SafeFeed uses the OpenAI Assistant API to retrieve the most relevant policies for a given content, ensuring moderation decisions align with community guidelines.
- **Sentiment Analysis**: SafeFeed utilizes the VaderSentiment library to analyze the sentiment (positive, negative, or neutral) of user-generated content, providing insights into the emotional tone.
- **User Notification**: When content is moderated, SafeFeed notifies the author, explaining the reason for removal and the violated policy.
- **Data Processing Pipeline**: SafeFeed integrates with Mage AI, a data pipeline tool, to efficiently manage tasks like data collection, content analysis, sentiment analysis, and data storage.
- **Data Storage**: SafeFeed stores processed data, including moderated content, violation categories, sentiment analysis results, and user information, in Snowflake for easy access and analysis.
- **User Interface**: SafeFeed provides a user-friendly interface built with Streamlit, allowing business users and subreddit moderators to customize the platform, define custom policies, and access moderation insights.
- **Policy Guide Chatbot**: SafeFeed offers a chatbot powered by the OpenAI Assistant API to help users understand platform policies through natural language queries.
- **AI-Generated Image Detection**: SafeFeed integrates with Sight Engine to identify and provide context for AI-generated images associated with posts.

## Architecture Diagram

![Architecture](https://github.com/LakshmanRaajS/Safe-Feed/assets/114884510/ba539c18-34fd-4c0c-af7b-d3cecbdea714)

## Getting Started

1. Clone the repository: `git clone https://github.com/your-username/SafeFeed.git`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Create a `.env` file in the root directory with the following structure:

```
OPENAI_ASSISTANT_ID=''
OPENAI_API_KEY=''
REDDIT_CLIENT_ID=''
REDDIT_CLIENT_SECRET=''
REDDIT_USER_AGENT=''
REDDIT_USERNAME=''
REDDIT_PASSWORD=''
SNOWFLAKE_USERNAME=''
SNOWFLAKE_PASSWORD=''
SNOWFLAKE_ACCOUNT=''
SNOWFLAKE_DATABASE=''
SNOWFLAKE_SCHEMA=''
```

4. Set up the Mage AI project and add the following secrets:
   - OPENAI_ASSISTANT_ID
   - OPENAI_API_KEY
   - REDDIT_CLIENT_ID
   - REDDIT_CLIENT_SECRET
   - REDDIT_USER_AGENT
   - REDDIT_USERNAME
   - REDDIT_PASSWORD
   - SNOWFLAKE_USERNAME
   - SNOWFLAKE_PASSWORD
   - SNOWFLAKE_ACCOUNT
   - SNOWFLAKE_DATABASE
   - SNOWFLAKE_SCHEMA
   - SIGHTENGINE_API_USER
   - SIGHTENGINE_API_SECRET
5. Run the application: `streamlit run app.py`

## Resources

- [Application Link](http://35.237.36.236:8502/)
- [Application Demo](https://www.youtube.com/watch?v=AWAqV3wDaXg)
