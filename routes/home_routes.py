# home_routes.py
from flask import Blueprint, render_template, request
from list_adm.topheroes_pop import get_available_dates

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/')
def index():
    return render_template('home.html')

@home_bp.route('/topheroes', methods=["GET"])
def top_heroes():
    ano = request.args.get("ano")
    mes = request.args.get("mes")
    dia = request.args.get("dia")  # formato YYYY-MM-DD

    # Só usado se quiser popular ainda algum dropdown antigo
    datas = get_available_dates()  

    # Anos disponíveis — pode ser dinâmico se quiser (ex: do banco)
    anos_disponiveis = [2024, 2025]

    meses_disponiveis = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    return render_template(
        'top_heroes.html',
        data_selecionada=dia,
        ano_selecionado=ano,
        mes_selecionado=mes,
        anos_disponiveis=anos_disponiveis,
        meses_disponiveis=meses_disponiveis,
        datas=datas  # pode remover se não estiver mais usando
    )


@home_bp.route('/players')
def players():
    from list_adm.topplayers_pop import get_top_players
    players_data = get_top_players()
    return render_template('player.html', players=players_data)
