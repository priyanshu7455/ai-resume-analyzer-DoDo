import os
from azure.storage.blob import BlobServiceClient

connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

container_name = "resumes"

blob_service_client = BlobServiceClient.from_connection_string(connect_str)

def upload_to_blob(file_name, file_data):
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=file_name
    )

    blob_client.upload_blob(file_data, overwrite=True)

    return f"Uploaded {file_name} successfully"