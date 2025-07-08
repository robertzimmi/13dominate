# tokens_box.py
import json
import os

TOKEN_FILE = 'box_tokens.json'

def save_tokens(access_token, refresh_token):
    with open(TOKEN_FILE, 'w') as f:
        json.dump({'access_token': access_token, 'refresh_token': refresh_token}, f)

def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        raise Exception("Token não encontrado. Autentique via /auth primeiro.")
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    return data['access_token'], data['refresh_token']
