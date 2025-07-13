from db import db_utils
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_hero_stats_by_date(data):
    conn = db_utils.connect_db()
    cur = conn.cursor()
    start = time.time()

    # Join entre a view e a tabela eventos para filtrar pela data
    query = '''
        SELECT DISTINCT ON (v."Hero", v."event_id")  
    v."Hero",
    v."hero_image",
    v."qtdplayers" AS total_uses,  -- aqui uso qtdplayers que conta jogadores distintos
    v."wins" AS total_wins,
    v."rounds_played" AS total_rounds,
    v."winrate" AS win_rate_percent
FROM v_hero_stats_mat v
JOIN eventos e ON v.event_id = e.id
WHERE e.data = %s;

    '''
    cur.execute(query, (data,))
    resultado = cur.fetchall()

    print("Tempo só query+fetch:", time.time() - start)
    cur.close()
    conn.close()
    return tuple(resultado)  # Imutável para cache


@lru_cache(maxsize=1)
def get_available_dates():
    conn = db_utils.connect_db()
    cur = conn.cursor()

    # Datas disponíveis agora vêm da tabela eventos
    query = 'SELECT DISTINCT data FROM eventos ORDER BY data DESC;'
    cur.execute(query)
    datas = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return tuple(datas)  # Imutável para cache
