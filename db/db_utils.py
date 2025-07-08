import psycopg2
import csv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
import time
from io import StringIO
import pandas as pd
from flask import session, flash
from datetime import datetime


def connect_db():
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    return conn

def disconnect_db(conn):
    if conn:
        conn.close()

def insert_heroes_from_csv(file, data, loja, formato, cur):
    t_start = time.time()
    usuario = session.get("usuario", "desconhecido")

    content = file.read()
    lines = content.strip().splitlines()

    corrected_rows = []
    for i, line in enumerate(lines[1:], start=2):
        parts = line.split(',', 3)
        if len(parts) == 4:
            player_name = parts[0].strip().strip('"')
            player_id = parts[1].strip().strip('"')
            country = parts[2].strip().strip('"')
            hero = parts[3].strip().strip('"')
            corrected_rows.append([
                player_name, player_id, country, hero,
                data, loja, formato, usuario
            ])

    if not corrected_rows:
        flash("❗ Nenhuma linha válida encontrada no CSV.", "warning")
        raise ValueError("Nenhuma linha válida encontrada no CSV.")

    flash(f"📄 Linhas válidas para inserção: {len(corrected_rows)}", "info")

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')
    writer.writerows(corrected_rows)
    buffer.seek(0)

    cur.copy_from(
        buffer,
        'heroes',
        sep='\t',
        columns=('PlayerName', 'PlayerID', 'Country', 'Hero', 'Data', 'Loja', 'Formato', 'usuario')
    )
    return "Dados inseridos com sucesso na tabela heroes!"

def insert_pairings_from_csv(file, data, loja, formato, cur):
    t_start = time.time()
    usuario = session.get("usuario", "desconhecido")

    df = pd.read_csv(file, encoding='utf-8-sig', dtype=str)

    # Acrescenta colunas fixas
    df['Data'] = data
    df['Loja'] = loja
    df['Formato'] = formato
    df['usuario'] = usuario

    # Ordena e seleciona colunas da tabela pairings
    df = df[['Round', 'Table', 'Player 1 Name', 'Player 1 ID',
             'Player 2 Name', 'Player 2 ID', 'Result',
             'Data', 'Loja', 'Formato', 'usuario']]
    df = df.fillna('').astype(str)

    buffer = StringIO()
    df.to_csv(buffer, sep='\t', index=False, header=False, quoting=csv.QUOTE_NONE, escapechar='\\')
    buffer.seek(0)

    cur.copy_from(
        buffer,
        'pairings',
        sep='\t',
        columns=('Round', 'Table', 'Player1Name', 'Player1ID',
                 'Player2Name', 'Player2ID', 'Result',
                 'Data', 'Loja', 'Formato', 'usuario')
    )

    return "Dados inseridos com sucesso na tabela pairings!"

def insert_standings_from_csv(file, data, loja, formato, cur):
    t_start = time.time()
    usuario = session.get("usuario", "desconhecido")

    df = pd.read_csv(file, encoding='utf-8-sig', dtype=str)

    df['Data'] = data
    df['Loja'] = loja
    df['Formato'] = formato
    df['usuario'] = usuario

    # Renomeia colunas para as do banco
    df = df[['Rank', 'Name', 'Player ID', 'Wins', 'Data', 'Loja', 'Formato', 'usuario']]
    df = df.rename(columns={'Player ID': 'PlayerID'})
    df = df.fillna('').astype(str)

    buffer = StringIO()
    df.to_csv(buffer, sep='\t', index=False, header=False, quoting=csv.QUOTE_NONE, escapechar='\\')
    buffer.seek(0)

    cur.copy_from(
        buffer,
        'standings',
        sep='\t',
        columns=('Rank', 'Name', 'PlayerID', 'Wins', 'Data', 'Loja', 'Formato', 'usuario')
    )

    return "Dados inseridos com sucesso na tabela standings!"

def insert_calendar_entry(data, loja, cur):
    usuario = session.get("usuario", "desconhecido")

    cur.execute("SELECT 1 FROM calendar WHERE data = %s AND loja = %s", (data, loja))
    exists = cur.fetchone()

    if not exists:
        loja_lower = loja.lower()
        if "bolovo" in loja_lower:
            cor = 'blue'
        elif "caverna" in loja_lower:
            cor = 'red'
        elif "arena" in loja_lower:
            cor = 'orange'
        else:
            cor = 'blue'

        cur.execute(
            "INSERT INTO calendar (data, loja, cor, usuario) VALUES (%s, %s, %s, %s)",
            (data, loja, cor, usuario)
        )
        return "Evento adicionado ao calendário com sucesso!"
    else:
        return "Evento já existe no calendário. Nenhuma ação foi tomada."
def get_box_tokens(cur):
    """
    Retorna access_token, refresh_token, client_id e client_secret da tabela token.
    """
    cur.execute("SELECT access_token, refresh_token, client_id, client_secret FROM token ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        return row[0], row[1], row[2], row[3]
    else:
        return None, None, None, None

def update_box_tokens(access_token, refresh_token, cur):
    """
    Atualiza access_token e refresh_token na tabela token.
    """
    usuario = session.get("usuario", "desconhecido")
    cur.execute("""
        UPDATE token SET access_token = %s, refresh_token = %s, updated_at = %s, usuario = %s
        WHERE id = (SELECT id FROM token ORDER BY id DESC LIMIT 1)
    """, (access_token, refresh_token, datetime.utcnow(), usuario))
