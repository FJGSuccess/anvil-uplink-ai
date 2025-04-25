import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Load credentials from service account JSON path stored in an environment variable
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')  # NEW: dynamic loading

if SERVICE_ACCOUNT_FILE is None:
    raise Exception("❌ SERVICE_ACCOUNT_FILE environment variable not set!")

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('drive', 'v3', credentials=credentials)

FOLDER_NAME = 'AI Knowledge base'

def get_folder_id(folder_name):
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    return folders[0]['id'] if folders else None

def download_folder_files(folder_id, local_folder='knowledge_base'):
    os.makedirs(local_folder, exist_ok=True)
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])

    for file in files:
        file_id = file['id']
        file_name = file['name']
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(os.path.join(local_folder, file_name), 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        print(f"Downloaded: {file_name}")

def sync_books():
    folder_id = get_folder_id(FOLDER_NAME)
    if folder_id:
        download_folder_files(folder_id)
        return "✅ Files downloaded from Google Drive."
    return "⚠️ Folder not found in Drive."
