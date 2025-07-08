from datetime import datetime
from flask import Blueprint, jsonify, render_template, request
from db import db_utils

api_topplayers = Blueprint('api_topplayers', __name__)

def fetch_top_players_from_db():
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

def fetch_player_metrics(player_name):
    sql = """
WITH date_filters AS (
  SELECT
    CURRENT_DATE AS today,
    date_trunc('month', CURRENT_DATE) AS first_day_current_month,
    date_trunc('month', CURRENT_DATE) - interval '1 month' AS first_day_last_month
),

player_standings AS (
  SELECT
    *,
    CAST("Wins" AS INTEGER) AS wins_int,
    date_trunc('month', CAST("Data" AS DATE)) AS month
  FROM standings
  WHERE "Name" = %(player_name)s
),

player_pairings AS (
  SELECT
    *,
    date_trunc('month', CAST("Data" AS DATE)) AS month
  FROM pairings
  WHERE "Player1Name" = %(player_name)s OR "Player2Name" = %(player_name)s
),

last_month_data AS (
  SELECT
    SUM(wins_int) AS total_wins_last_month,
    MAX(wins_int) AS max_wins_last_month,
    COUNT(*) AS total_events_last_month
  FROM player_standings s
  JOIN date_filters df ON s.month = df.first_day_last_month
),

last_month_rodadas AS (
  SELECT
    COUNT(*) AS total_rodadas_last_month
  FROM player_pairings p
  JOIN date_filters df ON p.month = df.first_day_last_month
),

current_month_data AS (
  SELECT
    SUM(wins_int) AS total_wins_current_month,
    MAX(wins_int) AS max_wins_current_month,
    COUNT(*) AS total_events_current_month
  FROM player_standings s
  JOIN date_filters df ON s.month = df.first_day_current_month
),

current_month_rodadas AS (
  SELECT
    COUNT(*) AS total_rodadas_current_month
  FROM player_pairings p
  JOIN date_filters df ON p.month = df.first_day_current_month
)

SELECT
  COALESCE(lm.total_wins_last_month, 0),
  COALESCE(lm.total_events_last_month, 0),
  COALESCE(lm.max_wins_last_month, 0),
  COALESCE(lr.total_rodadas_last_month, 0),
  COALESCE(cm.total_wins_current_month, 0),
  COALESCE(cm.total_events_current_month, 0),
  COALESCE(cm.max_wins_current_month, 0),
  COALESCE(cr.total_rodadas_current_month, 0),
  CASE WHEN lr.total_rodadas_last_month > 0
       THEN ROUND(100.0 * lm.total_wins_last_month / lr.total_rodadas_last_month, 2)
       ELSE 0 END,
  CASE WHEN cr.total_rodadas_current_month > 0
       THEN ROUND(100.0 * cm.total_wins_current_month / cr.total_rodadas_current_month, 2)
       ELSE 0 END

FROM last_month_data lm
CROSS JOIN last_month_rodadas lr
CROSS JOIN current_month_data cm
CROSS JOIN current_month_rodadas cr;
"""

    conn = db_utils.connect_db()
    cur = conn.cursor()
    cur.execute(sql, {'player_name': player_name})
    result = cur.fetchone()
    cur.close()
    db_utils.disconnect_db(conn)

    keys = [
        'wins_last_month', 'events_last_month', 'max_wins_last_month', 'rodadas_last_month',
        'wins_current_month', 'events_current_month', 'max_wins_current_month', 'rodadas_current_month',
        'winrate_last_month', 'winrate_current_month'
    ]

    if result:
        return dict(zip(keys, result))
    else:
        return dict.fromkeys(keys, 0)

@api_topplayers.route('/api/topplayers')
def get_top_players():
    players = fetch_top_players_from_db()
    return jsonify(players)

@api_topplayers.route('/playerprofile')
def player_profile():
    player_name = request.args.get("name")
    show_all = request.args.get("show_all") == "1"

    if not player_name:
        return render_template("playerprofile.html", error="Nome do jogador não fornecido.")

    players = fetch_top_players_from_db()
    player = next((p for p in players if p['name'] == player_name), None)

    if not player:
        return render_template("playerprofile.html", error="Jogador não encontrado.")

    metrics = fetch_player_metrics(player_name)
    mes_extenso = datetime.now().strftime('%B').capitalize()

    player_heroes = fetch_all_heroes_for_player(player_name) if show_all else fetch_current_month_heroes_for_player(player_name)
    next_player = players[(players.index(player) + 1) % len(players)]

    chart_labels, chart_wins = get_player_wins_data(player_name, show_all)

    return render_template("playerprofile.html",
                           player=player,
                           next_player=next_player,
                           player_heroes=player_heroes,
                           mes_extenso=mes_extenso,
                           show_all=show_all,
                           chart_labels=chart_labels,
                           chart_wins=chart_wins,
                           **metrics)


@api_topplayers.route('/api/player_chart_data')
def api_player_chart_data():
    player_name = request.args.get("name")
    show_all = request.args.get("show_all") == "1"

    conn = db_utils.connect_db()
    cur = conn.cursor()

    if show_all:
        query = """
            SELECT
                CAST("Data" AS date) AS data,
                SUM(CAST("Wins" AS INTEGER)) AS wins
            FROM standings
            WHERE "Name" = %s
            GROUP BY data
            ORDER BY data
        """
    else:
        query = """
            SELECT
                CAST("Data" AS date) AS data,
                SUM(CAST("Wins" AS INTEGER)) AS wins
            FROM standings
            WHERE "Name" = %s AND CAST("Data" AS date) >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY data
            ORDER BY data
        """

    cur.execute(query, (player_name,))
    results = cur.fetchall()
    cur.close()
    db_utils.disconnect_db(conn)

    data = {
        'labels': [row[0].strftime("%d/%m") for row in results],
        'wins': [int(row[1]) for row in results]
    }
    return jsonify(data)


def fetch_all_heroes_for_player(player_name):
    sql = """
    WITH hero_data AS (
        SELECT
            h."Hero" AS hero,
            CAST(s."Wins" AS INTEGER) AS wins,
            s."PlayerID",
            s."Data",
            s."Loja",
            s."Formato"
        FROM standings s
        JOIN heroes h ON s."PlayerID" = h."PlayerID" 
            AND s."Data" = h."Data" 
            AND s."Loja" = h."Loja" 
            AND s."Formato" = h."Formato"
        WHERE h."PlayerName" = %s
    ),
    hero_aggregates AS (
        SELECT
            hero,
            SUM(wins) AS total_wins,
            COUNT(DISTINCT ( "Data" || '-' || "Loja" || '-' || "Formato" )) AS armorys
        FROM hero_data
        GROUP BY hero
    ),
    hero_rounds AS (
        SELECT
            h."Hero" AS hero,
            COUNT(*) AS total_rounds
        FROM pairings p
        JOIN heroes h ON (
            (p."Player1ID" = h."PlayerID" OR p."Player2ID" = h."PlayerID")
            AND p."Data" = h."Data"
            AND p."Loja" = h."Loja"
            AND p."Formato" = h."Formato"
        )
        WHERE h."PlayerName" = %s
        GROUP BY h."Hero"
    )
    SELECT
        ha.hero,
        ha.total_wins AS wins,
        ha.armorys,
        COALESCE(hr.total_rounds, 0) - ha.total_wins AS losses,
        CASE 
          WHEN COALESCE(hr.total_rounds, 0) > 0 
          THEN ROUND(100.0 * ha.total_wins::numeric / hr.total_rounds, 2) 
          ELSE 0 
        END AS winrate
    FROM hero_aggregates ha
    LEFT JOIN hero_rounds hr ON ha.hero = hr.hero
    ORDER BY wins DESC;
    """

    conn = db_utils.connect_db()
    cur = conn.cursor()
    cur.execute(sql, (player_name, player_name))
    rows = cur.fetchall()
    cur.close()
    db_utils.disconnect_db(conn)

    heroes = []
    for row in rows:
        heroes.append({
            'name': row[0],
            'wins': int(row[1]),
            'armorys': int(row[2]),
            'losses': int(row[3]),
            'winrate': float(row[4])
        })
    return heroes

def fetch_current_month_heroes_for_player(player_name):
    sql = """
    WITH date_filter AS (
        SELECT date_trunc('month', CURRENT_DATE) AS this_month
    ),
    hero_data AS (
        SELECT
            h."Hero" AS hero,
            CAST(s."Wins" AS INTEGER) AS wins,
            s."PlayerID",
            s."Data",
            s."Loja",
            s."Formato"
        FROM standings s
        JOIN heroes h ON s."PlayerID" = h."PlayerID" 
            AND s."Data" = h."Data" 
            AND s."Loja" = h."Loja" 
            AND s."Formato" = h."Formato"
        JOIN date_filter df ON date_trunc('month', CAST(s."Data" AS DATE)) = df.this_month
        WHERE h."PlayerName" = %s
    ),
    hero_aggregates AS (
        SELECT
            hero,
            SUM(wins) AS total_wins,
            COUNT(DISTINCT ( "Data" || '-' || "Loja" || '-' || "Formato" )) AS armorys
        FROM hero_data
        GROUP BY hero
    ),
    hero_rounds AS (
        SELECT
            h."Hero" AS hero,
            COUNT(*) AS total_rounds
        FROM pairings p
        JOIN heroes h ON (
            (p."Player1ID" = h."PlayerID" OR p."Player2ID" = h."PlayerID")
            AND p."Data" = h."Data"
            AND p."Loja" = h."Loja"
            AND p."Formato" = h."Formato"
        )
        JOIN date_filter df ON date_trunc('month', CAST(p."Data" AS DATE)) = df.this_month
        WHERE h."PlayerName" = %s
        GROUP BY h."Hero"
    )
    SELECT
        ha.hero,
        ha.total_wins AS wins,
        ha.armorys,
        COALESCE(hr.total_rounds, 0) - ha.total_wins AS losses,
        CASE 
          WHEN COALESCE(hr.total_rounds, 0) > 0 
          THEN ROUND(100.0 * ha.total_wins::numeric / hr.total_rounds, 2) 
          ELSE 0 
        END AS winrate
    FROM hero_aggregates ha
    LEFT JOIN hero_rounds hr ON ha.hero = hr.hero
    ORDER BY wins DESC;
    """

    conn = db_utils.connect_db()
    cur = conn.cursor()
    cur.execute(sql, (player_name, player_name))
    rows = cur.fetchall()
    cur.close()
    db_utils.disconnect_db(conn)

    heroes = []
    for row in rows:
        heroes.append({
            'name': row[0],
            'wins': int(row[1]),
            'armorys': int(row[2]),
            'losses': int(row[3]),
            'winrate': float(row[4])
        })
    return heroes

def get_player_wins_data(player_name, show_all=False):
    conn = db_utils.connect_db()
    cur = conn.cursor()

    if show_all:
        query = """
            SELECT
                CAST("Data" AS date) AS data,
                SUM(CAST("Wins" AS INTEGER)) AS wins
            FROM standings
            WHERE "Name" = %s
            GROUP BY data
            ORDER BY data
        """
        cur.execute(query, (player_name,))
    else:
        query = """
            SELECT
                CAST("Data" AS date) AS data,
                SUM(CAST("Wins" AS INTEGER)) AS wins
            FROM standings
            WHERE "Name" = %s AND CAST("Data" AS date) >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY data
            ORDER BY data
        """
        cur.execute(query, (player_name,))

    results = cur.fetchall()
    cur.close()
    db_utils.disconnect_db(conn)

    labels = [row[0].strftime("%d/%m") for row in results]
    wins = [int(row[1]) if row[1] is not None else 0 for row in results]

    return labels, wins

@api_topplayers.route('/api/player_heroes_data')
def api_player_heroes_data():
    player_name = request.args.get("name")
    show_all = request.args.get("show_all") == "1"

    if not player_name:
        return jsonify([])

    if show_all:
        heroes = fetch_all_heroes_for_player(player_name)
    else:
        heroes = fetch_current_month_heroes_for_player(player_name)

    return jsonify(heroes)
