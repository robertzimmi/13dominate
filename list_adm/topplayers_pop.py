from db import db_utils

def get_top_players():
    conn = db_utils.connect_db()
    cur = conn.cursor()

    query = """
    SELECT
        name,
        total_partidas,
        armorys_jogados,
        wins,
        losses,
        ROUND(100.0 * wins / NULLIF(wins + losses, 0), 0) AS win_rate
    FROM v_player_stats
    ORDER BY win_rate DESC
    """

    cur.execute(query)
    rows = cur.fetchall()

    cur.close()
    db_utils.disconnect_db(conn)

    players = []
    for row in rows:
        players.append({
            'name': row[0],
            'total_partidas': row[1],
            'armorys_jogados': row[2],
            'wins': row[3],
            'losses': row[4],
            'win_rate': int(row[5]) if row[5] is not None else 0
        })

    return players
