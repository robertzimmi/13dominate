# home_routes.py
from flask import Blueprint, render_template, request, jsonify
from list_adm.topheroes_pop import get_available_dates
from datetime import datetime

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/')
def index():
    return render_template('home.html')

from datetime import datetime

@home_bp.route('/topheroes', methods=["GET"])
def top_heroes():
    ano = request.args.get("ano", "2025")
    mes = request.args.get("mes", str(datetime.now().month))  # garantir string
    dia = request.args.get("dia")

    # Pega as datas disponíveis do banco
    todas_datas = get_available_dates()

    datas_filtradas = []
    for d in todas_datas:
        # Se vier string, converte para datetime
        if isinstance(d, str):
            try:
                data_obj = datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                continue  # pula datas inválidas
        else:
            data_obj = d  # já é datetime

        if data_obj.year == int(ano) and data_obj.month == int(mes):
            datas_filtradas.append(data_obj)

    return render_template(
        'top_heroes.html',
        data_selecionada=dia,
        ano_selecionado=ano,
        mes_selecionado=mes,
        datas_filtradas=datas_filtradas,
    )


@home_bp.route('/datas', methods=['GET'])
def datas():
    ano = request.args.get("ano")
    mes = request.args.get("mes")

    if not ano or not mes:
        return jsonify([])

    todas_datas = get_available_dates()

    datas_filtradas = []
    for d in todas_datas:
        if isinstance(d, str):
            try:
                data_obj = datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                continue
        else:
            data_obj = d

        if data_obj.year == int(ano) and data_obj.month == int(mes):
            datas_filtradas.append(data_obj.strftime("%Y-%m-%d"))

    return jsonify(datas_filtradas)



@home_bp.route('/players')
def players():
    from list_adm.topplayers_pop import get_top_players
    players_data = get_top_players()
    return render_template('player.html', players=players_data)

@home_bp.route('/aprender')
def aprender():
    
    return render_template('aprender.html')
