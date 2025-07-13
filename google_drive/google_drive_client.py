# google_drive/google_drive_client.py
import os
from io import BytesIO
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN')
TOKEN_URI = 'https://oauth2.googleapis.com/token'

def get_service():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name, parent_id=None):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)', pageSize=10).execute()
    folders = results.get('files', [])

    if folders:
        return folders[0]['id']
    
    metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        metadata['parents'] = [parent_id]
    
    folder = service.files().create(body=metadata, fields='id').execute()
    return folder.get('id')

def upload_to_drive(file_stream: BytesIO, file_name: str, root_folder: str, subfolder: str):
    try:
        service = get_service()

        # 1. Criar ou pegar a pasta da loja (root_folder)
        root_id = get_or_create_folder(service, root_folder)

        # 2. Criar ou pegar a subpasta dentro dela
        subfolder_id = get_or_create_folder(service, subfolder, parent_id=root_id)

        # 3. Verifica se o arquivo já existe
        query = f"name = '{file_name}' and '{subfolder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        media = MediaIoBaseUpload(file_stream, mimetype='text/csv', resumable=True)

        if files:
            # Atualizar
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
            return f"♻️ Arquivo '{file_name}' atualizado na pasta '{root_folder}/{subfolder}'."
        else:
            # Enviar novo
            file_metadata = {
                'name': file_name,
                'parents': [subfolder_id]
            }
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return f"✅ Arquivo '{file_name}' enviado para '{root_folder}/{subfolder}'."
    except Exception as e:
        return f"❌ Erro ao enviar para o Google Drive: {repr(e)}"
