from datetime import timedelta
from google.cloud import storage
import os


# Set up Google Application Credentials for authentication
current_dir = os.path.dirname(os.path.realpath(__file__))
service_account_path = os.path.join(current_dir, 'cred', 'service_account.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path

# Initialize the Google Cloud Storage client
client = storage.Client()

# Set the name of your Google Cloud Storage bucket
BUCKET_NAME = 'scp_bucket'  # Replace with your actual GCS bucket name

def upload_to_gcp(file):
    try:
        # Specify the Google Cloud Storage bucket
        bucket = client.bucket(BUCKET_NAME)

        # Create a new blob (object) in the bucket
        blob = bucket.blob(file.filename)

        # Upload the file to the bucket
        blob.upload_from_file(file, content_type='application/pdf')

        # Generate a signed URL valid for 15 minutes
        signed_url = blob.generate_signed_url(
            expiration=timedelta(minutes=15),  # URL will be valid for 15 minutes
            method='GET'  # HTTP method allowed on the signed URL (GET for downloading)
        )

        print(f"File {file.filename} uploaded successfully. Signed URL: {signed_url}")
        return signed_url

    except Exception as e:
        print(f"Error uploading to GCP: {e}")
        return None