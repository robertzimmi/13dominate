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
    print(f"[GoogleDrive] 🔍 Procurando pasta: '{folder_name}'", end="")
    if parent_id:
        print(f" dentro da pasta pai ID: {parent_id}")
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents"
    else:
        print(" na raiz do Drive")
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and 'root' in parents"


    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, parents)',
        pageSize=10
    ).execute()

    folders = results.get('files', [])
    if folders:
        folder = folders[0]
        print(f"[GoogleDrive] ✅ Pasta existente: '{folder['name']}' (ID: {folder['id']})")
        return folder['id']

    # Criar pasta
    metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        metadata['parents'] = [parent_id]

    print(f"[GoogleDrive] ➕ Pasta não encontrada. Criando '{folder_name}'", end="")
    if parent_id:
        print(f" dentro da pasta pai ID: {parent_id}")
    else:
        print(" na raiz do Drive")

    folder = service.files().create(body=metadata, fields='id').execute()

    if 'id' in folder:
        print(f"[GoogleDrive] ✅ Pasta criada: '{folder_name}' (ID: {folder['id']})")
        return folder['id']
    else:
        error_msg = f"Erro ao criar a pasta '{folder_name}', resposta: {folder}"
        print(f"[GoogleDrive] ❌ {error_msg}")
        raise RuntimeError(error_msg)

def upload_to_drive(file_stream: BytesIO, file_name: str, root_folder: str, subfolder: str):
    try:
        service = get_service()
        print(f"[UPLOAD] 📁 Root folder: {root_folder}")
        print(f"[UPLOAD] 📂 Subfolder: {subfolder}")
        print(f"[UPLOAD] 📄 Arquivo: {file_name}")

        # 1. Criar ou pegar a pasta da loja (root_folder)
        root_id = get_or_create_folder(service, root_folder)

        # 2. Criar ou pegar a subpasta dentro dela
        subfolder_id = get_or_create_folder(service, subfolder, parent_id=root_id)

        # 3. Verifica se o arquivo já existe na subpasta
        query = f"name = '{file_name}' and '{subfolder_id}' in parents and trashed = false"
        print(f"[UPLOAD] 🔍 Verificando existência do arquivo com query: {query}")
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        print(f"[UPLOAD] 🔎 Arquivos encontrados: {len(files)}")

        media = MediaIoBaseUpload(file_stream, mimetype='text/csv', resumable=True)

        if files:
            # Atualizar
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
            print(f"[UPLOAD] ♻️ Arquivo atualizado: {file_name}")
            return f"♻️ Arquivo '{file_name}' atualizado na pasta '{root_folder}/{subfolder}'."
        else:
            # Enviar novo
            file_metadata = {
                'name': file_name,
                'parents': [subfolder_id]
            }
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"[UPLOAD] ✅ Arquivo enviado: {file_name}")
            return f"✅ Arquivo '{file_name}' enviado para '{root_folder}/{subfolder}'."

    except Exception as e:
        print(f"[UPLOAD] ❌ Erro: {repr(e)}")
        return f"❌ Erro ao enviar para o Google Drive: {repr(e)}"

# google_drive_client.py

def archive_drive_folder_by_date(data_str):
    service = get_service()
    parent_names = ['ARENA', 'BOLOVO', 'CAVERNA']

    # Buscar ID da pasta "DELETADO"
    query_deleted = (
    "name = 'DELETADO' and mimeType = 'application/vnd.google-apps.folder' "
    "and trashed = false and 'root' in parents"
)

    deleted_res = service.files().list(q=query_deleted, fields="files(id, name)").execute()
    deleted_folders = deleted_res.get("files", [])
    
    if not deleted_folders:
        raise Exception("❌ Pasta 'DELETADO' não encontrada na raiz do Google Drive.")

    deleted_folder_id = deleted_folders[0]["id"]

    for loja in parent_names:
        print(f"\n🔎 Buscando pasta raiz da loja: {loja}")
        query_raiz = f"name = '{loja}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res = service.files().list(q=query_raiz, fields="files(id, name)").execute()
        pastas_raiz = res.get("files", [])

        if not pastas_raiz:
            print(f"⚠️ Loja {loja} não encontrada no Drive.")
            continue

        raiz_id = pastas_raiz[0]["id"]
        prefixo = f"{loja}_{data_str}_"

        query_subpasta = (
            f"'{raiz_id}' in parents and "
            f"name contains '{data_str}' and "
            f"mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )

        subpastas = service.files().list(q=query_subpasta, fields="files(id, name, parents)").execute().get("files", [])

        if not subpastas:
            print(f"📁 Nenhuma subpasta com data {data_str} dentro de {loja}")
            continue

        for pasta in subpastas:
            nome_original = pasta["name"]
            if nome_original.startswith(prefixo):
                novo_nome = nome_original + "_deleted"
                pasta_id = pasta["id"]
                parent_id = pasta["parents"][0]["id"]

                # Renomear a pasta
                service.files().update(fileId=pasta_id, body={"name": novo_nome}).execute()
                print(f"✏️ Renomeado: {nome_original} ➡️ {novo_nome}")

                # Mover para pasta DELETADO
                service.files().update(
                    fileId=pasta_id,
                    addParents=deleted_folder_id,
                    removeParents=parent_id,
                    fields='id, parents'
                ).execute()
                print(f"📦 Movido para pasta 'DELETADO'")
            else:
                print(f"⏩ Ignorando pasta '{nome_original}' (prefixo diferente)")
