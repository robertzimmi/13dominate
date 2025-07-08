from db import db_utils
from functools import lru_cache
import time
@lru_cache(maxsize=100)
def get_hero_stats_by_date(data):
    conn = db_utils.connect_db()
    cur = conn.cursor()
    start = time.time()
    cur.execute('SELECT "hero_name","hero_image","total_uses","total_wins","total_rounds","win_rate_percent" FROM v_hero_stats_mat  WHERE "Data" = %s;', (data,))
    resultado = cur.fetchall()
    print("Tempo só query+fetch:", time.time() - start)
    cur.close()
    conn.close()
    return tuple(resultado)  # Imutável para cache



@lru_cache(maxsize=1)
def get_available_dates():
    conn = db_utils.connect_db()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT "Data" FROM heroes ORDER BY "Data" DESC;')
    datas = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return tuple(datas)  # Precisa ser imutável para cache



