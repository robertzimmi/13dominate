from flask import Blueprint, request, current_app, render_template , redirect, url_for, flash, session
from boxsdk import OAuth2
from box_integration.box_client import save_tokens_to_db

from db.db_utils import connect_db, disconnect_db
import bcrypt


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/')
def auth_start():
    oauth = OAuth2(
        client_id=current_app.config['BOX_CLIENT_ID'],
        client_secret=current_app.config['BOX_CLIENT_SECRET']
    )
    auth_url, _ = oauth.get_authorization_url('http://localhost:5000/auth/callback')
    return f'<a href="{auth_url}">Clique para autorizar o app no Box</a>'

@auth_bp.route('/callback')
def auth_callback():
    code = request.args.get('code')
    oauth = OAuth2(
        client_id=current_app.config['BOX_CLIENT_ID'],
        client_secret=current_app.config['BOX_CLIENT_SECRET']
    )
    access_token, refresh_token = oauth.authenticate(code)
    save_tokens_to_db(access_token, refresh_token)
    return "✅ Autenticado com sucesso! Tokens salvos."


from flask import request, make_response

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        senha = request.form.get('senha', '').strip()
        lembrar = request.form.get('lembrar') == 'on'

        if not usuario or not senha:
            flash('Preencha todos os campos.', 'error')
            return redirect(url_for('auth.login'))

        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("SELECT senha, precisa_trocar_senha FROM usuario WHERE usuario = %s", (usuario,))
            resultado = cur.fetchone()
        except Exception as e:
            flash('Erro ao acessar o banco de dados.', 'error')
            print(f"[ERRO DB] {e}")
            resultado = None
        finally:
            cur.close()
            disconnect_db(conn)

        if resultado:
            senha_hash, precisa_trocar = resultado
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                session['usuario'] = usuario
                session.permanent = lembrar

                resp = redirect(url_for('base'))

                if lembrar:
                    resp.set_cookie('usuario_cookie', usuario, max_age=60*60*24*30)  # 30 dias
                else:
                    resp.set_cookie('usuario_cookie', '', expires=0)  # remove

                #flash('Login realizado com sucesso!', 'success')

                if precisa_trocar:
                    flash('Você precisa alterar sua senha antes de continuar.', 'warning')
                    return redirect(url_for('auth.alterar_senha'))

                return resp
            else:
                flash('Senha incorreta.', 'error')
        else:
            flash('Usuário não encontrado.', 'error')

        return redirect(url_for('auth.login'))

    usuario_cookie = request.cookies.get('usuario_cookie', '')
    lembrar = True if usuario_cookie else False
    print(f"[DEBUG] Cookie recebido: {usuario_cookie}")
    print(f"[DEBUG] Lembrar está como: {lembrar}")

    return render_template('login.html', usuario_cookie=usuario_cookie, lembrar=lembrar)


@auth_bp.route('/alterar_senha', methods=['GET', 'POST'])
def alterar_senha():
    if 'usuario' not in session:
        flash('Você precisa estar logado para alterar sua senha.', 'warning')
        print("[DEBUG] Nenhum usuário na sessão.")
        return redirect(url_for('auth.login'))

    print(f"[DEBUG] Usuário na sessão: {session['usuario']}")

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha', '').strip()
        confirmar = request.form.get('confirmar', '').strip()

        print(f"[DEBUG] Nova senha recebida: {nova_senha}")
        print(f"[DEBUG] Confirmação recebida: {confirmar}")

        if not nova_senha or not confirmar:
            flash('Preencha todos os campos.', 'error')
            print("[DEBUG] Campos de senha vazios.")
            return redirect(url_for('auth.alterar_senha'))

        if nova_senha != confirmar:
            flash('As senhas não coincidem.', 'error')
            print("[DEBUG] As senhas não coincidem.")
            return redirect(url_for('auth.alterar_senha'))

        senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"[DEBUG] Senha hash gerada: {senha_hash}")

        conn = connect_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE usuario
                SET senha = %s, precisa_trocar_senha = FALSE
                WHERE usuario = %s
            """, (senha_hash, session['usuario']))
            conn.commit()

            print("[DEBUG] UPDATE executado no banco.")
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('base'))

        except Exception as e:
            print(f"[ERRO AO ATUALIZAR SENHA] {e}")
            flash('Erro ao atualizar a senha.', 'error')

        finally:
            cur.close()
            disconnect_db(conn)
            print("[DEBUG] Conexão com o banco encerrada.")

    return render_template('alterar_senha.html')





@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)  # Remove apenas o dado de login
    flash('Você saiu da conta.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    mensagem = None
    if request.method == 'POST':
        usuario = request.form.get('usuario')

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuario WHERE usuario = %s", (usuario,))
        resultado = cur.fetchone()

        if resultado:
            senha_padrao = 'senha1234'
            senha_hash = bcrypt.hashpw(senha_padrao.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            cur.execute("""
                UPDATE usuario
                SET precisa_trocar_senha = TRUE, senha = %s
                WHERE usuario = %s
            """, (senha_hash, usuario))
            conn.commit()
            mensagem = "Senha redefinida. Use 'senha1234' para entrar e altere sua senha ao acessar o sistema."
        else:
            mensagem = "Usuário não encontrado."

        cur.close()
        disconnect_db(conn)

    return render_template('esqueci_senha.html', mensagem=mensagem)
