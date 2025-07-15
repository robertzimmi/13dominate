# home_routes.py
from flask import Blueprint, render_template, request
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
    mes = request.args.get("mes", datetime.now().month)
    dia = request.args.get("dia")

    # Pega as datas disponíveis do banco
    todas_datas = get_available_dates()

    # Filtra as datas para o ano/mês selecionado
    datas_filtradas = [
        d for d in todas_datas 
        if d.year == int(ano) and d.month == int(mes)
    ]

    return render_template(
        'top_heroes.html',
        data_selecionada=dia,
        ano_selecionado=ano,
        mes_selecionado=mes,
        datas_filtradas=datas_filtradas,
    )



@home_bp.route('/players')
def players():
    from list_adm.topplayers_pop import get_top_players
    players_data = get_top_players()
    return render_template('player.html', players=players_data)
