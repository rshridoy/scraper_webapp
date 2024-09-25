import requests
from bs4 import BeautifulSoup
import re
import time
import pdfplumber
import os
from PyPDF2 import PdfFileReader
from io import BytesIO

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


def extract_text_from_pdf(pdf_url):
    try:
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with BytesIO(response.content) as pdf_file:
                with pdfplumber.open(pdf_file) as pdf:
                    pdf_text = ""
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            pdf_text += text
                        else:
                            print(f"Page {page.page_number} has no extractable text.")
            
            pdf_text = clean_and_normalize_text(pdf_text)
            return pdf_text if pdf_text.strip() else None
        else:
            print(f"Failed to retrieve PDF from {pdf_url}, Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error processing PDF from {pdf_url}: {e}")
        return None
