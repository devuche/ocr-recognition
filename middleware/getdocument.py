from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
storage_account = os.environ.get('STORAGE_ACCOUNT')
storage_key = os.environ.get('STORAGE_KEY')
container_name = os.environ.get('CONTAINER_NAME')

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient(account_url=f"https://{storage_account}.blob.core.windows.net", credential=f"{storage_key}")

def generate_blob_url(blob_name):
    sas_token = generate_blob_sas(
        account_name=storage_account,
        container_name=container_name,
        blob_name=blob_name,
        account_key=storage_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=5)  # SAS token valid for 1 hour
    )
    blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
    return blob_url
