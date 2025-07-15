from flask import Blueprint, request, current_app, render_template , redirect, url_for, flash, session
from db.db_utils import connect_db, disconnect_db
import bcrypt


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')



from flask import request, make_response


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()
        lembrar = request.form.get('lembrar') == 'on'

        print(f"[DEBUG] Tentativa de login - email: '{email}', lembrar: {lembrar}")

        if not email or not senha:
            flash('Preencha todos os campos.', 'error')
            print("[DEBUG] Campos email ou senha vazios.")
            return redirect(url_for('auth.login'))

        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT 
                    u.encrypted_password, 
                    p.precisa_trocar_senha 
                FROM auth.users u
                JOIN perfil_usuarios p ON p.id = u.id
                WHERE u.email = %s
            """, (email,))

            resultado = cur.fetchone()
            print(f"[DEBUG] Resultado do banco: {resultado}")

        except Exception as e:
            flash('Erro ao acessar o banco de dados.', 'error')
            print(f"[ERRO DB] {e}")
            resultado = None
        finally:
            cur.close()
            disconnect_db(conn)
            print("[DEBUG] Conexão com o banco encerrada.")

        if resultado:
            senha_hash, precisa_trocar = resultado
            print(f"[DEBUG] senha_hash: {senha_hash}, precisa_trocar: {precisa_trocar}")
            # Se senha_hash vier em bytes, converta para string, e vice-versa
            if isinstance(senha_hash, memoryview):  # em alguns drivers pode vir assim
                senha_hash = senha_hash.tobytes().decode('utf-8')

            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                print("[DEBUG] Senha conferida com sucesso.")
                session['usuario'] = email
                session.permanent = lembrar

                resp = redirect(url_for('base'))

                if lembrar:
                    resp.set_cookie('email_cookie', email, max_age=60*60*24*30)  # 30 dias
                else:
                    resp.set_cookie('email_cookie', '', expires=0)  # remove

                if precisa_trocar:
                    flash('Você precisa alterar sua senha antes de continuar.', 'warning')
                    cur.close()
                    disconnect_db(conn)
                    print("[DEBUG] Usuário precisa trocar senha. Redirecionando para alterar_senha.")
                    return redirect(url_for('auth.alterar_senha'))


                return resp
            else:
                flash('Senha incorreta.', 'error')
                print("[DEBUG] Senha incorreta.")
        else:
            flash('Email não encontrado.', 'error')
            print("[DEBUG] Email não encontrado no banco.")

        return redirect(url_for('auth.login'))

    # Para o método GET (exibir formulário)
    email_cookie = request.cookies.get('email_cookie', '')
    lembrar = True if email_cookie else False
    print(f"[DEBUG] Cookie recebido: {email_cookie}")
    print(f"[DEBUG] Lembrar está como: {lembrar}")

    return render_template('login.html', email_cookie=email_cookie, lembrar=lembrar)


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
        UPDATE auth.users
        SET encrypted_password = %s
        WHERE email = %s
    """, (senha_hash, session['usuario']))

            # Atualiza precisa_trocar_senha na tabela perfil_usuarios
            cur.execute("""
                UPDATE perfil_usuarios p
                SET precisa_trocar_senha = FALSE
                FROM auth.users u
                WHERE u.id = p.id AND u.email = %s
            """, (session['usuario'],))
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
    return redirect(url_for('home_bp.index'))


from flask import flash, redirect, url_for

@auth_bp.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    mensagem = None
    sucesso = False  # controle do sucesso do commit

    if request.method == 'POST':
        usuario = request.form.get('email')
        print(f"[DEBUG] Email recebido no formulário: {usuario}")

        conn = connect_db()
        cur = conn.cursor()

        try:
            cur.execute("SELECT * FROM auth.users WHERE email = %s", (usuario,))
            resultado = cur.fetchone()
            print(f"[DEBUG] Resultado da consulta SELECT auth.users: {resultado}")

            if resultado:
                senha_padrao = 'senha1234'
                senha_hash = bcrypt.hashpw(senha_padrao.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                print(f"[DEBUG] Senha padrão hash gerada: {senha_hash}")

                cur.execute("""
                    UPDATE auth.users
                    SET encrypted_password = %s
                    WHERE email = %s
                """, (senha_hash, usuario))
                print("[DEBUG] UPDATE em auth.users executado.")

                cur.execute("""
                    UPDATE perfil_usuarios p
                    SET precisa_trocar_senha = TRUE
                    FROM auth.users u
                    WHERE u.id = p.id AND u.email = %s
                """, (usuario,))
                print("[DEBUG] UPDATE em perfil_usuarios executado.")

                conn.commit()
                print("[DEBUG] Commit realizado com sucesso.")

                mensagem = "Senha redefinida. Use 'senha1234' para entrar e altere sua senha ao acessar o sistema."
                sucesso = True
            else:
                mensagem = "Usuário não encontrado."
                print("[DEBUG] Usuário não encontrado no banco.")

        except Exception as e:
            print(f"[ERRO] Exceção durante esqueci_senha: {e}")
            mensagem = "Ocorreu um erro ao tentar redefinir a senha."

        finally:
            cur.close()
            disconnect_db(conn)
            print("[DEBUG] Conexão com o banco encerrada.")

    if sucesso:
        flash(mensagem)
        return redirect(url_for('home_bp.index'))
    else:
        return render_template('esqueci_senha.html', mensagem=mensagem)
