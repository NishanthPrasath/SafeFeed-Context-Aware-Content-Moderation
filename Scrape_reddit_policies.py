from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import snowflake.connector
import os



url = "https://www.redditinc.com/policies/content-policy"
headers = {'User-Agent': 'Mozilla/5.0'}

response = requests.get(url, headers=headers)
href_dict = {}
content_dict = {}

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    content_div = soup.find('div', id='content')
    
    if content_div:
        links = content_div.find_all('a')
        for link in links:
            if link.text and link.get('href'):
                href_dict[link.text.strip()] = link.get('href').strip()
    
    # IDs of divs containing the main content based on your provided HTML structure
    content_ids = ['content']

    formatted_content = ""  # Initialize an empty string to accumulate content
    
    for content_id in content_ids:

        content_div = soup.find('div', id=content_id)
        
        if content_div:
            for child in content_div.descendants:
                if child.name in ['h1', 'h2', 'h3']:
                    formatted_content += child.text # Add headings
                elif child.name == 'p':
                    formatted_content += child.text # Add paragraphs
                elif child.name == 'li':
                    formatted_content += child.text # Add list items
            
            content_dict['home'] = formatted_content

        else:
            print(f"Div with id '{content_id}' not found.")
else:
    print(f"Failed to fetch the webpage, status code: {response.status_code}")


for name, href in href_dict.items():
    print(f"{name}: {href}")

for key, url in href_dict.items():
    # Initialize a Selenium WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    driver.get(url)

    time.sleep(5)

    # Extract the page source and parse it with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find the main article body
    article_body = soup.find('div', class_='lt-article__body')

    if article_body:
        # Extract the text from the article body
        content_dict[key] = article_body.get_text(separator=' ', strip=True)
        print(f"{key}: Content extracted.")  # Output the extracted text
    else:
        content_dict[key] = "Content division not found."
        print(f"{key}: Content division not found.")

    # Sleep for 5 seconds before loading the next URL
    time.sleep(5)

    driver.quit()

# Now content_dict contains a note for each href, keyed by the original link text
for name, content_note in content_dict.items():
    print(f"{name}: {content_note}")


# Specify the filename
filename = "reddit_policies.csv"

# Writing to CSV
with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['key', 'value']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for key, value in content_dict.items():
        writer.writerow({'key': key, 'value': value})

print(f"CSV file '{filename}' created successfully.")
