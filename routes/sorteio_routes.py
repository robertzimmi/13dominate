from flask import Blueprint, render_template, request, jsonify
from db.db_utils import connect_db

sorteio_bp = Blueprint("sorteio_bp", __name__)

@sorteio_bp.route("/admin/sorteio", methods=["GET"])
def sorteio_page():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT e.id, e.data, e.formato, e.loja
        FROM eventos e
        ORDER BY e.data DESC
    """)

    eventos = [
        {
            "id": row[0],
            "data": row[1].strftime("%Y-%m-%d"),
            "formato": row[2],
            "store_name": row[3]
        }
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return render_template("sorteio.html", eventos=eventos)


@sorteio_bp.route("/admin/sorteio/participantes", methods=["POST"])
def sorteio_participantes():
    data = request.get_json()
    event_ids = data.get("event_ids", [])
    if not event_ids:
        return jsonify({})
    try:
        event_ids = list(map(int, event_ids))
        conn = connect_db()
        cur = conn.cursor()
        query = """
            SELECT s.event_id, p.name
            FROM standings s
            JOIN players p ON s."PlayerID" = p.id
            WHERE s.event_id = ANY(%s)
              AND p.name IS NOT NULL
        """
        cur.execute(query, (event_ids,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        participantes = {}
        for event_id, nome in rows:
            participantes.setdefault(str(event_id), []).append(nome)

        return jsonify(participantes)
    except Exception as e:
        print(f"[ERRO] Ao buscar participantes: {e}")
        return jsonify({})

@sorteio_bp.route("/admin/sorteio/sortear", methods=["POST"])
def realizar_sorteio():
    data = request.get_json()
    participantes = data.get("participantes", [])
    nomes_unicos = data.get("nomes_unicos", True)

    if nomes_unicos:
        participantes = list(set(participantes))

    if len(participantes) < 2:
        return jsonify({"error": "Participantes insuficientes para sortear."}), 400

    import random
    vencedor = random.choice(participantes)
    backup = random.choice([p for p in participantes if p != vencedor])

    # Imprimir participantes no terminal
    print(f"[SORTEIO] Participantes: {participantes}")
    print(f"[SORTEIO] Vencedor: {vencedor}")
    print(f"[SORTEIO] Backup: {backup}")

    return jsonify({"vencedor": vencedor, "backup": backup})