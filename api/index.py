from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Olá do Flask na Vercel!'

# NÃO use app.run()
# Apenas exporte o app, pois o Vercel vai chamá-lo
