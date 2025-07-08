import os
from io import BytesIO
from boxsdk import OAuth2, Client
from db.db_utils import get_box_tokens, update_box_tokens
from db.db_utils import connect_db, disconnect_db

def save_tokens_to_db(access_token, refresh_token):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            update_box_tokens(access_token, refresh_token, cur)
            conn.commit()
            print("✅ Tokens atualizados no banco de dados.")
    finally:
        disconnect_db(conn)

def load_tokens_from_db():
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            return get_box_tokens(cur)
    finally:
        disconnect_db(conn)

def upload_to_box(file_stream: BytesIO, file_name: str, folder_name: str) -> str:
    print(f"🔄 Iniciando upload do arquivo '{file_name}' para a pasta '{folder_name}' no Box...")

    access_token, refresh_token, client_id, client_secret = load_tokens_from_db()
    if not all([access_token, refresh_token, client_id, client_secret]):
        print("❌ Tokens ou credenciais não encontrados no banco.")
        return "❌ Tokens ou credenciais não configurados no banco de dados."

    oauth = OAuth2(
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
        refresh_token=refresh_token,
        store_tokens=save_tokens_to_db
    )

    try:
        client = Client(oauth)
        print("✅ Cliente Box inicializado.")

        root_folder = client.folder('0')
        folder_id = None

        for item in root_folder.get_items():
            if item.type == 'folder' and item.name == folder_name:
                folder_id = item.id
                print(f"✅ Pasta '{folder_name}' encontrada. ID: {folder_id}")
                break

        if folder_id is None:
            print(f"📁 Pasta '{folder_name}' não encontrada. Criando...")
            folder_id = root_folder.create_subfolder(folder_name).id
            print(f"✅ Pasta criada. ID: {folder_id}")

        folder = client.folder(folder_id)

        existing_file = None
        for item in folder.get_items():
            if item.type == 'file' and item.name == file_name:
                existing_file = item
                print(f"♻️ Arquivo existente encontrado: {file_name}")
                break

        file_stream.seek(0)

        if existing_file:
            print(f"⬆️ Atualizando conteúdo de '{file_name}'...")
            updated_file = existing_file.update_contents(file_stream)
            return f"✅ Arquivo '{updated_file.name}' atualizado com sucesso na pasta '{folder_name}'!"
        else:
            print(f"⬆️ Enviando novo arquivo '{file_name}'...")
            uploaded_file = folder.upload_stream(file_stream, file_name)
            return f"✅ Arquivo '{uploaded_file.name}' enviado para a pasta '{folder_name}' no Box com sucesso!"

    except Exception as e:
        print(f"❌ Exceção ao enviar arquivo para o Box: {repr(e)}")
        return f"❌ Erro ao enviar arquivo para o Box: {repr(e)}"
