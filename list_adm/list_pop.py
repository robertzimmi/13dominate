from db import db_utils

def get_heroes():
    conn = db_utils.connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM heroes ORDER BY data_inserida DESC')
    heroes = cur.fetchall()
    cur.close()
    conn.close()
    return heroes

def get_standings():
    conn = db_utils.connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM standings ORDER BY data_inserida DESC')
    standings = cur.fetchall()
    cur.close()
    conn.close()
    return standings

def get_pairings():
    conn = db_utils.connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM pairings ORDER BY data_inserida DESC')
    pairings = cur.fetchall()
    cur.close()
    conn.close()
    return pairings
