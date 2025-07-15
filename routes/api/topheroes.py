from flask import Blueprint, request, jsonify
from list_adm.topheroes_pop import get_hero_stats_by_filters

api_topheroes_bp = Blueprint('api_topheroes_bp', __name__)

@api_topheroes_bp.route('/api/topheroes', methods=['GET'])
def api_top_heroes():
    ano = request.args.get("ano")
    mes = request.args.get("mes")
    dia = request.args.get("dia")  # dia completo no formato YYYY-MM-DD

    # Nenhum filtro? Retorna erro
    if not (ano or mes or dia):
        return jsonify({"error": "É necessário fornecer ao menos um filtro: ano, mês ou dia."}), 400

    herois = get_hero_stats_by_filters(ano=ano, mes=mes, dia=dia)

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

    return jsonify(herois_json)
