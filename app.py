import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Importa blueprints
from routes.calendar_routes import calendar_bp
from routes.upload_routes import upload_bp
from routes.auth_routes import auth_bp
from routes.delete_routes import delete_bp
from routes.lista_routes import lista_bp
from routes.api.lista_api import lista_api
from routes.home_routes import home_bp
from routes.api.topheroes import api_topheroes_bp
from routes.sorteio_routes import sorteio_bp
from routes.api.topplayers import api_topplayers
from routes.deck_routes import decks_bp
from routes.ligacommoner_routes import ligacommoner_bp


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')  # configure sua SECRET_KEY no .env para produção

csrf = CSRFProtect(app)

# Variável global para template footer
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}



@app.route('/base')
def base():
    if 'usuario' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('base.html')





@app.route('/esqueci_senha')
def esqueci_senha():
    return render_template('esqueci_senha.html')


@app.route('/uploadcsv')
def uploadcsv():
    # Esta rota pode redirecionar para o blueprint /upload/
    return redirect(url_for('upload.upload_page'))

# Login simples
@app.route('/login', methods=['GET', 'POST'])
def login():
    usuario_cookie = session.get('usuario', '')

    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        lembrar = request.form.get('lembrar')

        # Validação simples — substitua por lógica real
        if usuario == 'admin' and senha == 'senha123':
            session['usuario'] = usuario if lembrar else ''
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home_bp.index'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html', usuario_cookie=usuario_cookie, lembrar=bool(usuario_cookie))

# Logout simples
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu da conta.', 'success')
    return redirect(url_for('home_bp.index'))

# Registrar blueprints
app.register_blueprint(delete_bp)
app.register_blueprint(calendar_bp)   # prefixo definido no próprio blueprint
app.register_blueprint(upload_bp)     # /upload
app.register_blueprint(auth_bp)
app.register_blueprint(lista_bp)
app.register_blueprint(lista_api)
app.register_blueprint(home_bp)
app.register_blueprint(api_topheroes_bp)
app.register_blueprint(api_topplayers)
app.register_blueprint(sorteio_bp)
app.register_blueprint(decks_bp)
app.register_blueprint(ligacommoner_bp)
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
