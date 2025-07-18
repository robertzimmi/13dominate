from flask import Blueprint, request, jsonify
from list_adm.topheroes_pop import get_hero_stats_by_filters

api_topheroes_bp = Blueprint('api_topheroes_bp', __name__)

@api_topheroes_bp.route('/api/topheroes', methods=['GET'])
def api_top_heroes():
    ano = request.args.get("ano")
    mes = request.args.get("mes")
    dia = request.args.get("dia")
    formato = request.args.get("formato")

    if not (ano or mes or dia):
        return jsonify({"error": "É necessário fornecer ao menos um filtro: ano, mês ou dia."}), 400

    if dia:
        try:
            from datetime import datetime
            datetime.strptime(dia, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Parâmetro 'dia' inválido. Use formato YYYY-MM-DD."}), 400

    herois = get_hero_stats_by_filters(ano=ano, mes=mes, dia=dia, formato=formato)

    if not herois:
        return jsonify({
            "store_name": None,
            "herois": []
        })

    store_name = herois[0][6]

    herois_json = [
        {
            "hero_name": h[0],
            "hero_image": h[1],
            "total_uses": h[2],
            "total_wins": h[3],
            "total_rounds": h[4],
            "win_rate_percent": h[5]
        }
        for h in herois
    ]

    return jsonify({
        "store_name": store_name,
        "formato": formato,
        "herois": herois_json
    })

from list_adm.topheroes_pop import get_available_dates_by_filters

@api_topheroes_bp.route('/api/get_dates', methods=['GET'])
def get_dates():
    ano = request.args.get("ano")
    mes = request.args.get("mes")
    formato = request.args.get("formato", "todos")

    if not (ano and mes):
        return jsonify([])

    datas = get_available_dates_by_filters(ano, mes, formato)
    return jsonify(datas)
