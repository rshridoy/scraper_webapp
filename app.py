import threading
from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient, errors
from gcp_helpers import upload_to_gcp
from scraper import scrape_paragraphs, clean_and_normalize_text
import os
import time

app = Flask(__name__)

# MongoDB connection string (replace with your connection string)
CONNECTION_STRING = "mongodb+srv://test:test@cluster0.glcwxo4.mongodb.net/napa?retryWrites=true&w=majority&appName=Cluster0"

# Create the MongoDB client and connect to the 'scp' database once at app startup
client = MongoClient(CONNECTION_STRING)
db = client['scp']


@app.route('/')
def index():
    # Count of processed and unprocessed links
    processed_count = db.processed_data.count_documents({})
    unprocessed_count = db.urls_pdfs.count_documents({})
    return render_template('index.html', processed_count=processed_count, unprocessed_count=unprocessed_count)

@app.route('/upload', methods=['POST'])
def upload_files():
    if db is None:
        return "Database connection failed", 500

    urls = request.form.get('urls').splitlines()  # Get URLs from form input
    files = request.files.getlist('pdfs')  # Get list of uploaded PDF files

    # MongoDB collection for URLs and PDFs
    urls_pdfs_collection = db['urls_pdfs']

    # Upload PDFs to Google Cloud Storage and save links in MongoDB under "urls_pdfs" collection
    for file in files:
        if file:
            # Upload the PDF to GCP and get the GCP link
            pdf_url = upload_to_gcp(file)
            
            # Insert the PDF information into the "urls_pdfs" collection
            urls_pdfs_collection.insert_one({
                'url': pdf_url,
                'type': 'pdf',  # Mark this as a PDF entry
                'processed': False  # PDF is not processed yet
            })

    # Save URLs to MongoDB under "urls_pdfs" collection
    for url in urls:
        if url:
            urls_pdfs_collection.insert_one({
                'url': url,
                'type': 'url',  # Mark this as a URL entry
                'processed': False  # URL is not processed yet
            })

    return redirect(url_for('index'))  # Redirect user to the index page after submission

def process_links_in_background():
    while True:
        # Fetch unprocessed URLs in LIFO order
        unprocessed_urls = db.urls_pdfs.find({'processed': False}).sort('_id', -1)

        for url_data in unprocessed_urls:
            url = url_data['url']
            print(f"Processing URL: {url}")

            paragraphs = scrape_paragraphs(url)

            # Save scraped data to MongoDB
            if paragraphs:
                db.processed_data.insert_one({'url': url, 'paragraphs': paragraphs})
                print(f"Inserted data for {url}")
            else:
                print(f"No data found for {url}")

            # Mark as processed
            db.urls_pdfs.update_one({'_id': url_data['_id']}, {'$set': {'processed': True}})
            print(f"Marked {url} as processed.")

        # Sleep for 5 seconds before processing again
        time.sleep(5)

# Start the background thread for processing links
def start_background_processing():
    thread = threading.Thread(target=process_links_in_background)
    thread.daemon = True  # Daemon threads exit when the main program exits
    thread.start()

if __name__ == '__main__':
    # Start background processing before running the app
    start_background_processing()

    # Run the Flask app
    app.run(debug=True)
