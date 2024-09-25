from google.cloud import storage
import os
# Set up Google Application Credentials for authentication
current_dir = os.path.dirname(os.path.realpath(__file__))
service_account_path = os.path.join(current_dir, 'cred', 'service_account.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
bucket_name = 'scp_bucket'

def upload_to_gcp(file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)
    return blob.public_url
