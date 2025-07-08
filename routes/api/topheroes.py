# api/topheroes.py
from flask import Blueprint, request, jsonify
from list_adm.topheroes_pop import get_hero_stats_by_date



api_topheroes_bp = Blueprint('api_topheroes_bp', __name__)

@api_topheroes_bp.route('/api/topheroes', methods=['GET'])
def api_top_heroes():
    data = request.args.get("data")
    if not data:
        return jsonify({"error": "data not provided"}), 400

    herois = get_hero_stats_by_date(data)
    herois_json = [
    {
        "hero_name": h[0],
        "hero_image": h[1],
        "total_uses": h[2],
        "total_wins": h[3],
        "total_rounds": h[4],  # se quiser usar depois
        "win_rate_percent": h[5]  # <- agora incluído
    }
    for h in herois
]
    return jsonify(herois_json)
