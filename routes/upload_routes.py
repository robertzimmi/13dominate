from flask import Blueprint, request, jsonify,render_template
from werkzeug.utils import secure_filename
from io import BytesIO, StringIO

from db.db_utils import (
    connect_db, disconnect_db,
    insert_heroes_from_csv,
    insert_standings_from_csv,
    insert_pairings_from_csv,
    insert_calendar_entry
)
from box_integration.box_client import upload_to_box
from utils.helpers import allowed_file

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')

@upload_bp.route('/', methods=['GET'])
def upload_page():
    return render_template('uploadcsv.html')

@upload_bp.route('/submit', methods=['POST'])
def upload_submit():
    conn = None
    try:
        # Validação dos campos
        required_fields = ['data', 'loja', 'formato']
        for field in required_fields:
            if not request.form.get(field):
                return jsonify({
                    "success": False,
                    "message": f"❌ Campo obrigatório '{field}' não foi fornecido."
                }), 400

        # Validação dos arquivos
        files = {}
        for key in ['heroes', 'standings', 'pairings']:
            f = request.files.get(key)
            if not f or f.filename == '':
                return jsonify({
                    "success": False,
                    "message": f"❌ Arquivo '{key}' não enviado."
                }), 400
            if not allowed_file(f.filename):
                return jsonify({
                    "success": False,
                    "message": f"❌ Arquivo inválido: {f.filename}. Apenas CSV permitido."
                }), 400
            files[key] = f

        data = request.form['data'].strip()
        loja = request.form['loja'].strip()
        formato = request.form['formato'].strip()
        pasta_box = f"{loja}_{data}_{formato}"

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("REFRESH MATERIALIZED VIEW v_hero_stats_mat;")
        # Processa CSVs
        result_heroes = insert_heroes_from_csv(
            StringIO(files['heroes'].read().decode('utf-8-sig')),
            data, loja, formato, cur
        )
        result_standings = insert_standings_from_csv(
            StringIO(files['standings'].read().decode('utf-8-sig')),
            data, loja, formato, cur
        )
        result_pairings = insert_pairings_from_csv(
            StringIO(files['pairings'].read().decode('utf-8-sig')),
            data, loja, formato, cur
        )
        calendar_result = insert_calendar_entry(data, loja, cur)

        # Upload para Box
        box_msgs = []
        for key in ['heroes', 'standings', 'pairings']:
            files[key].seek(0)
            msg = upload_to_box(BytesIO(files[key].read()), secure_filename(files[key].filename), pasta_box)
            box_msgs.append(msg)

        # Verifica falhas
        if any(m.startswith("❌") for m in box_msgs):
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "❌ Falha no upload para Box.",
                "box_errors": box_msgs
            }), 500

        # Commit final
        conn.commit()

        return jsonify({
            "success": True,
            "message": "✅ Dados enviados com sucesso!",
            "results": {
                "heroes": result_heroes,
                "standings": result_standings,
                "pairings": result_pairings,
                "calendar": calendar_result,
                "box": box_msgs
            }
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "message": f"❌ Erro geral: {repr(e)}"
        }), 500

    finally:
        if conn:
            disconnect_db(conn)
