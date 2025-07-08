from flask import Blueprint, request, jsonify
from db import db_utils

lista_api = Blueprint('lista_api', __name__)

# Funções auxiliares
def get_search_filter(search_value, fields):
    like = f'%{search_value}%'
    conditions = [f"{field} ILIKE %s" for field in fields]
    where_clause = " OR ".join(conditions)
    params = [like] * len(fields)
    return where_clause, params

def get_year_filter_clause():
    years = request.args.get('years')
    if not years or years == "*":
        return "", []

    year_list = [int(y.strip()) for y in years.split(',') if y.strip().isdigit()]
    if not year_list:
        return "", []

    placeholders = ','.join(['%s'] * len(year_list))
    clause = f"(EXTRACT(YEAR FROM \"Data\"::DATE) IN ({placeholders}))"
    return clause, year_list

# ========== HEROES ==========
@lista_api.route('/api/heroes')
def api_heroes():
    try:
        draw = int(request.args.get('draw', 1))
        search_value = request.args.get('search[value]', '')

        conn = db_utils.connect_db()
        cur = conn.cursor()

        cur.execute('SELECT COUNT(*) FROM heroes')
        records_total = cur.fetchone()[0]

        where_clauses = []
        params = []

        if search_value:
            clause, p = get_search_filter(search_value, ['"PlayerName"', '"Hero"', '"Loja"'])
            where_clauses.append(f"({clause})")
            params += p

        year_clause, year_params = get_year_filter_clause()
        if year_clause:
            where_clauses.append(year_clause)
            params += year_params

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        cur.execute(f"SELECT COUNT(*) FROM heroes {where_sql}", params)
        records_filtered = cur.fetchone()[0]

        query = f"""
            SELECT "PlayerName", "Hero", "Data", "Loja", "Formato"
            FROM heroes
            {where_sql}
        """
        cur.execute(query, params)
        rows = cur.fetchall()

        data = [{
            "player_name": r[0],
            "hero": r[1],
            "date": r[2],
            "store": r[3],
            "format": r[4],
        } for r in rows]

        cur.close()
        conn.close()

        return jsonify({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== STANDINGS ==========
@lista_api.route('/api/standings')
def api_standings():
    draw = int(request.args.get('draw', 1))
    search_value = request.args.get('search[value]', '')

    conn = db_utils.connect_db()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM standings')
    records_total = cur.fetchone()[0]

    where_clauses = []
    params = []

    if search_value:
        clause, p = get_search_filter(search_value, ['"Name"', '"Loja"'])
        where_clauses.append(f"({clause})")
        params += p

    year_clause, year_params = get_year_filter_clause()
    if year_clause:
        where_clauses.append(year_clause)
        params += year_params

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    cur.execute(f"SELECT COUNT(*) FROM standings {where_sql}", params)
    records_filtered = cur.fetchone()[0]

    query = f"""
        SELECT "Name", "Rank", "Wins", "Data", "Loja", "Formato"
        FROM standings
        {where_sql}
    """
    cur.execute(query, params)
    rows = cur.fetchall()

    data = [{
        "name": r[0],
        "rank": r[1],
        "wins": r[2],
        "date": r[3],
        "store": r[4],
        "format": r[5],
    } for r in rows]

    cur.close()
    conn.close()

    return jsonify({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })

# ========== PAIRINGS ==========
@lista_api.route('/api/pairings')
def api_pairings():
    draw = int(request.args.get('draw', 1))
    search_value = request.args.get('search[value]', '')

    conn = db_utils.connect_db()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM pairings')
    records_total = cur.fetchone()[0]

    where_clauses = []
    params = []

    if search_value:
        clause, p = get_search_filter(search_value, ['"Player1Name"', '"Player2Name"'])
        where_clauses.append(f"({clause})")
        params += p

    year_clause, year_params = get_year_filter_clause()
    if year_clause:
        where_clauses.append(year_clause)
        params += year_params

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    cur.execute(f"SELECT COUNT(*) FROM pairings {where_sql}", params)
    records_filtered = cur.fetchone()[0]

    query = f"""
        SELECT "Player1Name", "Round", "Player2Name", "Result", "Data", "Loja", "Formato"
        FROM pairings
        {where_sql}
    """
    cur.execute(query, params)
    rows = cur.fetchall()

    data = [{
        "player1": r[0],
        "round": r[1],
        "player2": r[2],
        "result": r[3],
        "date": r[4],
        "store": r[5],
        "format": r[6],
    } for r in rows]

    cur.close()
    conn.close()

    return jsonify({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })
