"""
blob_storage.py
---------------
Handles uploading resume PDFs to Azure Blob Storage.
Uses lazy initialization so the app doesn't crash at import
if the env variable hasn't loaded yet.
"""

import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

CONTAINER_NAME = "resumes"


def get_blob_client():
    """Create and return a BlobServiceClient — called lazily, not at import."""
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connect_str:
        raise EnvironmentError(
            "Missing AZURE_STORAGE_CONNECTION_STRING in environment variables."
        )
    return BlobServiceClient.from_connection_string(connect_str)


def upload_to_blob(file_name: str, file_data: bytes) -> str:
    """
    Upload a file to the 'resumes' container in Azure Blob Storage.

    Args:
        file_name: The blob name (e.g. 'resume.pdf').
        file_data: Raw bytes of the file.

    Returns:
        Success message string.
    """
    try:
        blob_service_client = get_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME,
            blob=file_name,
        )
        blob_client.upload_blob(file_data, overwrite=True)
        return f"✅ Uploaded {file_name} to Azure Blob Storage."
    except Exception as e:
        # Don't crash the whole app if upload fails — just warn
        return f"⚠️ Blob upload skipped: {e}"
