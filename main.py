from app import create_app, socketio
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

load_dotenv()

container_name = os.environ.get('CONTAINER_NAME')
connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(connection_string)


app = create_app()
if __name__ == '__main__':
    container_client = blob_service_client.get_container_client(container_name)
    if not container_client.exists():
        container_client.create_container()
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
