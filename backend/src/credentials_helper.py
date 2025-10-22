"""
Helper script to handle Google Cloud credentials for deployment
Supports both file-based and base64-encoded service account credentials
"""
import os
import json
import base64
import tempfile
from pathlib import Path


def get_google_credentials_path():
    """
    Get path to Google service account credentials.
    Supports two modes:
    1. File path from GOOGLE_APPLICATION_CREDENTIALS env var
    2. Base64-encoded JSON from GCP_SERVICE_ACCOUNT_JSON env var
    
    Returns:
        str: Path to the credentials JSON file
    """
    # Mode 1: Direct file path (local development)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        return creds_path
    
    # Mode 2: Base64-encoded JSON (production deployment)
    encoded_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if encoded_json:
        try:
            # Decode base64
            decoded_json = base64.b64decode(encoded_json).decode('utf-8')
            credentials_dict = json.loads(decoded_json)
            
            # Write to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
                prefix='gcp_credentials_'
            )
            json.dump(credentials_dict, temp_file)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            print(f"Error decoding GCP_SERVICE_ACCOUNT_JSON: {e}")
            raise
    
    # Fallback: Look for service account JSON in backend directory
    backend_dir = Path(__file__).parent.parent
    for json_file in backend_dir.glob("*.json"):
        if "service" in json_file.name.lower() or "hackathon" in json_file.name.lower():
            return str(json_file)
    
    raise ValueError(
        "No Google Cloud credentials found. Please set either:\n"
        "1. GOOGLE_APPLICATION_CREDENTIALS (path to JSON file), or\n"
        "2. GCP_SERVICE_ACCOUNT_JSON (base64-encoded JSON)"
    )


def get_credentials_dict():
    """
    Get Google credentials as a dictionary.
    
    Returns:
        dict: Service account credentials
    """
    creds_path = get_google_credentials_path()
    with open(creds_path, 'r') as f:
        return json.load(f)
