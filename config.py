import os
from dotenv import load_dotenv

load_dotenv()

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

    # Outras configs...
