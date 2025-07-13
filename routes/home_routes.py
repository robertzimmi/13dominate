# home_routes.py
from flask import Blueprint, render_template, request
from list_adm.topheroes_pop import get_available_dates

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/')
def index():
    return render_template('home.html')

@home_bp.route('/topheroes', methods=["GET", "POST"])
def top_heroes():
    datas = get_available_dates()
    data_selecionada = request.form.get("data") if request.method == "POST" else datas[0] if datas else None

    return render_template(
        'top_heroes.html',
        datas=datas,
        data_selecionada=data_selecionada
    )

@home_bp.route('/players')
def players():
    from list_adm.topplayers_pop import get_top_players
    players_data = get_top_players()
    return render_template('player.html', players=players_data)
