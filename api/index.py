from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify(message="Olá, Flask na Vercel funcionando!")

# Ponto obrigatório para Vercel
def handler(environ, start_response):
    from werkzeug.wrappers import Request, Response
    request = Request(environ)
    response = app.full_dispatch_request()
    return response(environ, start_response)