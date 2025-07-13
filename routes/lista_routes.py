from flask import Blueprint, render_template

lista_bp = Blueprint('lista_bp', __name__)

@lista_bp.route('/lista-adm')
def lista_adm():
    return render_template('listadm.html')  # sem dados
