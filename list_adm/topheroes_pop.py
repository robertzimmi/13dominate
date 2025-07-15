
from functools import lru_cache
from db.db_utils import connect_db, disconnect_db
import time

@lru_cache(maxsize=100)
def get_hero_stats_by_filters(ano=None, mes=None, dia=None):
    conn = connect_db()
    cur = conn.cursor()

    query = '''
        SELECT DISTINCT ON (v."Hero", v."event_id")
            v."Hero",
            v."hero_image",
            v."qtdplayers" AS total_uses,
            v."wins" AS total_wins,
            v."rounds_played" AS total_rounds,
            v."winrate" AS win_rate_percent,
            e.loja AS nome_loja
        FROM v_hero_stats_mat v
        JOIN eventos e ON v.event_id = e.id
        WHERE 1=1
    '''

    filtros = []
    params = []

    if ano:
        filtros.append("EXTRACT(YEAR FROM e.data) = %s")
        params.append(str(ano))
    if mes:
        filtros.append("EXTRACT(MONTH FROM e.data) = %s")
        params.append(str(mes))
    if dia:
        filtros.append("e.data = %s")
        params.append(dia)

    if filtros:
        query += " AND " + " AND ".join(filtros)

    query += " ORDER BY v.\"Hero\", v.\"event_id\""

    cur.execute(query, tuple(params))
    resultado = cur.fetchall()
    cur.close()
    conn.close()
    return resultado




@lru_cache(maxsize=1)
def get_available_dates():
    conn = connect_db()
    if conn is None:
        print("[ERROR] Falha ao conectar no banco de dados em get_available_dates.")
        return tuple()  # Retorna vazio para evitar quebrar a view

    try:
        cur = conn.cursor()
        query = 'SELECT DISTINCT data FROM eventos ORDER BY data DESC;'
        cur.execute(query)
        datas = [row[0] for row in cur.fetchall()]
        cur.close()
        return tuple(datas)
    except Exception as e:
        print(f"[ERROR] Erro ao buscar datas disponíveis: {e}")
        return tuple()
    finally:
        disconnect_db(conn)
