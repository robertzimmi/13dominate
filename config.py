import os
from dotenv import load_dotenv

if os.environ.get("RENDER") != "true":
    from dotenv import load_dotenv
    load_dotenv()  # só em dev 

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'devkey')
    BOX_CLIENT_ID = os.getenv('BOX_CLIENT_ID')
    BOX_CLIENT_SECRET = os.getenv('BOX_CLIENT_SECRET')

    # Banco de dados
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
    # Outras configs...
print("[DEBUG] CONFIG DB VARS:")
print(f"DB_HOST: {Config.DB_HOST}")
print(f"DB_PORT: {Config.DB_PORT}")
print(f"DB_NAME: {Config.DB_NAME}")
print(f"DB_USER: {Config.DB_USER}")
print(f"DB_PASSWORD: {'***' if Config.DB_PASSWORD else None}")