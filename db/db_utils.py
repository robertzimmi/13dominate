import psycopg2
import csv
import sys
import os
import socket
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
import time
from io import StringIO
import pandas as pd
from flask import session, flash
from datetime import datetime


def connect_db():
    host_ipv4 = socket.gethostbyname(Config.DB_HOST)
    conn = psycopg2.connect(
        host=host_ipv4,
        port=Config.DB_PORT,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    return conn

def disconnect_db(conn):
    if conn:
        conn.close()

def get_or_create_event(data, loja, formato, cur):
    try:
        cur.execute("SELECT id FROM eventos WHERE data = %s AND loja = %s AND formato = %s", (data, loja, formato))
        result = cur.fetchone()

        if result:
            print(f"[EVENTO EXISTENTE] ID: {result[0]} para {data}, {loja}, {formato}")
            return result[0]

        cur.execute(
            "INSERT INTO eventos (data, loja, formato) VALUES (%s, %s, %s) RETURNING id",
            (data, loja, formato)
        )
        new_id = cur.fetchone()[0]
        print(f"[NOVO EVENTO] Criado com ID: {new_id} para {data}, {loja}, {formato}")
        return new_id
    except Exception as e:
        print(f"[ERRO EVENTO] {repr(e)}")
        raise

def ensure_players_exist(player_ids, cur):
    # Verifica os player_ids que já existem (na coluna players.id)
    cur.execute(
        "SELECT id FROM players WHERE id::integer = ANY(%s);",
        (player_ids,)
    )
    existing = {row[0] for row in cur.fetchall()}

    missing = [pid for pid in player_ids if pid not in existing]

    for pid in missing:
        cur.execute(
            "INSERT INTO players (id) VALUES (%s) ON CONFLICT DO NOTHING;",
            (pid,)
        )


def insert_heroes_from_csv(file, event_id, cur):
    try:
        df = pd.read_csv(file, encoding='utf-8-sig', dtype=str)
        expected_cols = ['Player Name', 'Player ID', 'Country', 'Hero']
        missing = [c for c in expected_cols if c not in df.columns]

        if missing:
            raise ValueError(f"[HEROES] Colunas faltando: {missing}")

        df['Hero'] = df['Hero'].str.replace(' (LL)', '', regex=False)
        df['event_id'] = str(event_id)

        df = df.rename(columns={
            'Player Name': 'PlayerName',
            'Player ID': 'PlayerID'
        })

        df = df.fillna('').astype(str)
        df = df[['PlayerName', 'PlayerID', 'Country', 'Hero', 'event_id']]

        buffer = StringIO()
        df.to_csv(buffer, sep='\t', index=False, header=False, quoting=csv.QUOTE_NONE, escapechar='\\')
        buffer.seek(0)

        cur.copy_from(buffer, 'heroes', sep='\t',
                      columns=('PlayerName', 'PlayerID', 'Country', 'Hero', 'event_id'))

        flash(f"📄 {len(df)} linhas inseridas na tabela heroes!", "info")
        return "Dados inseridos com sucesso na tabela heroes!"
    except Exception as e:
        print(f"[ERRO HEROES] {repr(e)}")
        raise

def insert_pairings_from_csv(file, event_id, cur):
    try:
        df = pd.read_csv(file, encoding='utf-8-sig', dtype=str)
        expected_cols = ['Round', 'Table', 'Player 1 Name', 'Player 1 ID',
                         'Player 2 Name', 'Player 2 ID', 'Result']
        missing = [c for c in expected_cols if c not in df.columns]

        if missing:
            raise ValueError(f"[PAIRINGS] Colunas faltando: {missing}")

        df = df.fillna('')  # Substitui NaN por string vazia

        # Substituir 'None' ou '' por 'Bye' e 99999999
        bye_mask = (df['Player 2 Name'].str.strip().str.lower().isin(['', 'none'])) & (df['Player 2 ID'].str.strip() == '')

        df.loc[bye_mask, 'Player 2 Name'] = 'Bye'
        df.loc[bye_mask, 'Player 2 ID'] = '99999999'

        # Garantir que Player 2 ID esteja presente (tudo como string)
        df = df.astype(str)

        df['event_id'] = str(event_id)
        df = df.rename(columns={
            'Player 1 Name': 'Player1Name',
            'Player 1 ID': 'Player1ID',
            'Player 2 Name': 'Player2Name',
            'Player 2 ID': 'Player2ID'
        })

        df = df[['Round', 'Table', 'Player1Name', 'Player1ID',
                 'Player2Name', 'Player2ID', 'Result', 'event_id']]

        # Garantir que o jogador fictício Bye exista na tabela players
        cur.execute("""
            INSERT INTO players (id, name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (99999999, 'Bye'))

        buffer = StringIO()
        df.to_csv(buffer, sep='\t', index=False, header=False, quoting=csv.QUOTE_NONE, escapechar='\\')
        buffer.seek(0)

        cur.copy_from(buffer, 'pairings', sep='\t',
                      columns=('Round', 'Table', 'Player1Name', 'Player1ID',
                               'Player2Name', 'Player2ID', 'Result', 'event_id'))

        flash(f"📄 {len(df)} linhas inseridas na tabela pairings!", "info")
        return "Dados inseridos com sucesso na tabela pairings!"

    except Exception as e:
        print(f"[ERRO PAIRINGS] {repr(e)}")
        raise

def insert_standings_from_csv(file, event_id, cur):
    try:
        df = pd.read_csv(file, encoding='utf-8-sig', dtype=str)
        print("Colunas do DataFrame:", df.columns.tolist())

        expected_cols = ['Rank', 'Name', 'Player ID', 'Wins']
        missing_cols = [c for c in expected_cols if c not in df.columns]

        if missing_cols:
            flash(f"❗ Colunas faltando no CSV: {missing_cols}", "danger")
            raise ValueError(f"Colunas faltando no CSV: {missing_cols}")

        df['event_id'] = str(event_id)
        df = df[expected_cols + ['event_id']]
        df = df.rename(columns={'Player ID': 'PlayerID'})
        df = df.fillna('').astype(str)

        buffer = StringIO()
        df.to_csv(buffer, sep='\t', index=False, header=False, quoting=csv.QUOTE_NONE, escapechar='\\')
        buffer.seek(0)

        cur.copy_from(
            buffer,
            'standings',
            sep='\t',
            columns=('Rank', 'Name', 'PlayerID', 'Wins', 'event_id')
        )

        flash(f"📄 {len(df)} linhas inseridas na tabela standings!", "info")
        return "Dados inseridos com sucesso na tabela standings!"

    except Exception as e:
        print(f"[ERRO STANDINGS] {repr(e)}")
        flash(f"❌ Erro ao processar standings: {repr(e)}", "danger")
        raise



def insert_calendar_entry(data, loja, event_id, cur):
    # usuario = session.get("email_cookie", "desconhecido")  # remove essa linha, se não for mais usada

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
            cor = 'black'

        cur.execute("""
    INSERT INTO calendar (data, loja, cor, event_id)
    VALUES (%s, %s, %s, %s)
""", (data, loja, cor, event_id))
        return "Evento adicionado ao calendário com sucesso!"
    else:
        return "Evento já existe no calendário. Nenhuma ação foi tomada."



#def get_box_tokens(cur):
    """
    Retorna access_token, refresh_token, client_id e client_secret da tabela token.
    """
    cur.execute("SELECT access_token, refresh_token, client_id, client_secret FROM token ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        return row[0], row[1], row[2], row[3]
    else:
        return None, None, None, None

#def update_box_tokens(access_token, refresh_token, cur):
    """
    Atualiza access_token e refresh_token na tabela token.
    """
    usuario = session.get("email_cookie", "desconhecido")
    cur.execute("""
        UPDATE token SET access_token = %s, refresh_token = %s, updated_at = %s, usuario = %s
        WHERE id = (SELECT id FROM token ORDER BY id DESC LIMIT 1)
    """, (access_token, refresh_token, datetime.utcnow(), usuario))
