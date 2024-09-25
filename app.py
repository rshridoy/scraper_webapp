import threading
from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient, errors
from gcp_helpers import upload_to_gcp
from scraper import scrape_paragraphs, clean_and_normalize_text, extract_text_from_pdf
import os
import time

app = Flask(__name__)

# MongoDB connection string (replace with your connection string)
# CONNECTION_STRING = "mongodb+srv://test:test@cluster0.glcwxo4.mongodb.net/napa?retryWrites=true&w=majority&appName=Cluster0"
CONNECTION_STRING = "mongodb://localhost:27017/"
# Create the MongoDB client and connect to the 'scp' database once at app startup
client = MongoClient(CONNECTION_STRING)
db = client['scp']


@app.route('/')
def index():
    # Count of processed and unprocessed links
    processed_count = db.processed_data.count_documents({})
    unprocessed_count = db.urls_pdfs.count_documents({'processed': False})
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
        # Fetch unprocessed URLs and PDFs
        unprocessed_items = db.urls_pdfs.find({'processed': False})

        if db.urls_pdfs.count_documents({'processed': False}) == 0:
            print("No more unprocessed items. Stopping the background process.")
            break  # Exit the loop and stop the background process

        for item in unprocessed_items:
            url = item['url']
            print(f"Processing item: {url}")

            if item['type'] == 'url':
                # Scrape paragraphs from URL
                paragraphs = scrape_paragraphs(url)

                if paragraphs:
                    # Save scraped data to MongoDB
                    db.processed_data.insert_one({'url': url, 'paragraphs': paragraphs})
                    print(f"Inserted scraped data for {url}")
                else:
                    print(f"No data found for {url}")
            elif item['type'] == 'pdf':
                # Extract text from PDF
                pdf_text = extract_text_from_pdf(url)

                if pdf_text:
                    # Save extracted PDF data to MongoDB
                    db.processed_data.insert_one({'url': url, 'pdf_text': pdf_text})
                    print(f"Inserted extracted data for PDF {url}")
                else:
                    print(f"No text found for PDF {url}")

            # Mark the item as processed
            db.urls_pdfs.update_one({'_id': item['_id']}, {'$set': {'processed': True}})
            print(f"Marked {url} as processed.")

        # Sleep for 5 seconds before checking for new items again
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
