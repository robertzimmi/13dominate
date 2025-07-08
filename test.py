import os
import bcrypt
import psycopg2
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env (opcional, se estiver usando)
load_dotenv()

# Conecta ao banco de dados
def connect_db():
    required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"]
    for var in required_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"❌ Variável de ambiente não definida: {var}")
    
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432")
    )

# Desconecta do banco
def disconnect_db(conn):
    if conn:
        conn.close()

# Atualiza as senhas
def atualizar_senhas():
    conn = connect_db()
    cur = conn.cursor()

    # Pega todos os usuários e senhas
    cur.execute("SELECT usuario, senha FROM usuario")
    usuarios = cur.fetchall()

    atualizados = 0

    for usuario, senha in usuarios:
        if not senha.startswith('$2a$') and not senha.startswith('$2b$'):
            print(f"🔐 Atualizando senha do usuário: {usuario}")
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute("UPDATE usuario SET senha = %s WHERE usuario = %s", (senha_hash, usuario))
            atualizados += 1

    conn.commit()
    cur.close()
    disconnect_db(conn)

    print(f"✅ {atualizados} senha(s) atualizada(s) com sucesso.")

# Executa se for chamado diretamente
if __name__ == "__main__":
    atualizar_senhas()
