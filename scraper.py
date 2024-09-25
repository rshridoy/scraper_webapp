import requests
from bs4 import BeautifulSoup
import re
import time

def clean_and_normalize_text(text):
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def scrape_paragraphs(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            paragraph_texts = [clean_and_normalize_text(p.get_text().strip()) for p in paragraphs if p.get_text().strip()]
            time.sleep(5)
            return " ".join(paragraph_texts) if paragraph_texts else None
        else:
            print(f"Failed to retrieve {url}, Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
