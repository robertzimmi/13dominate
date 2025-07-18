from flask import Blueprint, render_template
from datetime import date
from db.db_utils import connect_db, disconnect_db

ligacommoner_bp = Blueprint('ligacommoner', __name__, url_prefix='/ligacommoner')

@ligacommoner_bp.route('/')
def ligacommoner_home():
    conn = connect_db()
    if not conn:
        return "Erro ao conectar ao banco de dados", 500

    cursor = conn.cursor()
    lojas = ['BOLOVO', 'ARENA', 'CAVERNA']
    dados = {}
    dados['herois_por_loja'] = {}

    data_inicio = date(2025, 6, 1)

    # Query jogadores (igual a sua)
    query_jogadores = """
    WITH eventos_filtrados AS (
      SELECT 
        e.id AS event_id,
        e.data,
        e.loja,
        e.formato,
        EXTRACT(MONTH FROM e.data) AS mes,
        EXTRACT(YEAR FROM e.data) AS ano
      FROM eventos e
      WHERE e.formato = 'COMMONER'
        AND e.loja = %s
        AND e.data BETWEEN %s AND CURRENT_DATE
    ),
    vitorias AS (
      SELECT 
        s."PlayerID",
        MAX(s."Name") AS player,
        SUM(s."Wins") AS total_wins,
        SUM(
          CASE 
            WHEN EXTRACT(MONTH FROM ef.data) = 6 AND EXTRACT(YEAR FROM ef.data) = 2025 THEN COALESCE(hp."062025", 0) * s."Wins"
            WHEN EXTRACT(MONTH FROM ef.data) = 7 AND EXTRACT(YEAR FROM ef.data) = 2025 THEN COALESCE(hp."072025", 0) * s."Wins"
            ELSE 0
          END
        ) AS pontos
      FROM standings s
      JOIN eventos_filtrados ef ON s.event_id = ef.event_id
      JOIN heroes h ON s."PlayerID" = h."PlayerID" AND s.event_id = h.event_id
      LEFT JOIN heroparametro hp ON h."Hero" = hp.hero
      GROUP BY s."PlayerID"
    ),
    rodadas AS (
      SELECT 
        p."Player1ID" AS player_id, COUNT(*) AS rounds
      FROM pairings p
      JOIN eventos_filtrados ef ON p.event_id = ef.event_id
      GROUP BY p."Player1ID"

      UNION ALL

      SELECT 
        p."Player2ID" AS player_id, COUNT(*) AS rounds
      FROM pairings p
      JOIN eventos_filtrados ef ON p.event_id = ef.event_id
      GROUP BY p."Player2ID"
    ),
    rodadas_somadas AS (
      SELECT 
        player_id,
        SUM(rounds) AS total_rounds
      FROM rodadas
      GROUP BY player_id
    )
    SELECT 
      v.player,
      v.total_wins,
      COALESCE(r.total_rounds, 0) AS total_rounds,
      ROUND(100.0 * v.total_wins / NULLIF(r.total_rounds, 0), 2) AS win_percent,
      ROUND(v.pontos, 2) AS pontos
    FROM vitorias v
    LEFT JOIN rodadas_somadas r ON v."PlayerID" = r.player_id
    ORDER BY pontos DESC, v.total_wins DESC;
    """

    # Query heróis por loja com % aparição e link da imagem
    query_herois = """
    WITH eventos_filtrados AS (
      SELECT e.id AS event_id, e.loja
      FROM eventos e
      WHERE e.formato = 'COMMONER' AND e.loja = %s AND e.data BETWEEN %s AND CURRENT_DATE
    ),
    herois_loja AS (
      SELECT h."Hero"
      FROM heroes h
      JOIN eventos_filtrados ef ON h.event_id = ef.event_id
    ),
    total_herois AS (
      SELECT COUNT(*) AS total FROM herois_loja
    ),
    herois_contados AS (
      SELECT h."Hero", COUNT(*) AS quantidade
      FROM heroes h
      JOIN eventos_filtrados ef ON h.event_id = ef.event_id
      GROUP BY h."Hero"
    )
    SELECT 
      hc."Hero" AS hero,
      COALESCE(a.link, '') AS img,
      ROUND(100.0 * hc.quantidade / NULLIF(t.total,0), 2) AS percent
    FROM herois_contados hc
    CROSS JOIN total_herois t
    LEFT JOIN arteheroes a ON hc."Hero" = a."Hero"
    ORDER BY percent DESC;
    """

    for loja in lojas:
        # Jogadores
        cursor.execute(query_jogadores, (loja, data_inicio))
        rows = cursor.fetchall()
        dados[loja] = [
            {
                'Player': r[0],
                'Wins': r[1],
                'Rounds': r[2],
                'WinPercent': r[3],
                'Pontos': r[4]
            }
            for r in rows
        ]

        # Heróis
        cursor.execute(query_herois, (loja, data_inicio))
        rows_herois = cursor.fetchall()
        dados['herois_por_loja'][loja] = [
            {
                'hero': r[0],
                'img': r[1] if r[1] else '/static/img/heroes/default.png',  # imagem default se faltar
                'percent': r[2]
            }
            for r in rows_herois
        ]

    cursor.close()
    disconnect_db(conn)

    return render_template('ligacommoner.html', dados=dados)
