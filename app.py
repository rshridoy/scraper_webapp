from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient
from gcp_helpers import upload_to_gcp
from scraper import scrape_paragraphs, clean_and_normalize_text
import os

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['your_database']

@app.route('/')
def index():
    # Count of processed and unprocessed links
    processed_count = db.processed.count_documents({})
    unprocessed_count = db.urls.count_documents({})
    return render_template('index.html', processed_count=processed_count, unprocessed_count=unprocessed_count)

@app.route('/upload', methods=['POST'])
def upload():
    urls = request.form.get('urls').splitlines()
    files = request.files.getlist('pdfs')

    # Upload PDFs to Google Cloud Storage and save links in MongoDB
    for file in files:
        if file:
            pdf_url = upload_to_gcp(file)
            db.pdfs.insert_one({'url': pdf_url})

    # Save URLs to MongoDB
    for url in urls:
        db.urls.insert_one({'url': url, 'processed': False})

    return redirect(url_for('index'))

@app.route('/process', methods=['GET'])
def process_links():
    # Fetch unprocessed URLs in LIFO order
    unprocessed_urls = db.urls.find({'processed': False}).sort('_id', -1)

    for url_data in unprocessed_urls:
        url = url_data['url']
        paragraphs = scrape_paragraphs(url)
        
        # Save scraped data to MongoDB
        db.processed.insert_one({'url': url, 'paragraphs': paragraphs})
        
        # Mark as processed
        db.urls.update_one({'_id': url_data['_id']}, {'$set': {'processed': True}})
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
