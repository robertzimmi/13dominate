from flask import Blueprint, render_template, current_app
from db.db_utils import connect_db

# ✅ Definindo o blueprint aqui mesmo
decks_bp = Blueprint('decks', __name__)

# Dados dos decks
deck_groups = {
    "Commoner": [
        {"name": "Ira, Crimson Haze", "url": "https://fabrary.net/decks/01JVBR8KT3C3563VNJPE5HEPT7"},
        {"name": "Enigma", "url": "https://fabrary.net/decks/01JVBVV6DDBY2ZBJB692EZFF55"},
        {"name": "Dash", "url": "https://fabrary.net/decks/01JVBSVY4TZ96QW52PKCMXB9QG"},
        {"name": "Briar", "url": "https://fabrary.net/decks/01JVBQB9B1EY1BM0RARVYH2YNR"},
        {"name": "Verdance", "url": "https://fabrary.net/decks/01J7SS3PPF5VYZPJZN503V9P8Y"},
        {"name": "Chane", "url": "https://fabrary.net/decks/01JVBQAPP2K35RQVY85XEWR4NK"}
    ],
    "CC AD upgrade": [
        {"name": "Ira, Scarlet Revenger", "url": "http://google.com"}
    ]
}

def get_hero_images():
    conn = connect_db()
    if not conn:
        return {}

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM arteheroes")
        data = {row[0]: row[1] for row in cursor.fetchall()}
        return data
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar imagens dos heróis: {e}")
        return {}
    finally:
        conn.close()


@decks_bp.route('/decks')
def decks():
    hero_images = get_hero_images()

    enriched_groups = {}
    for group_name, decks in deck_groups.items():
        enriched_decks = []
        for deck in decks:
            img = hero_images.get(deck['name'], 'default.jpg')
            enriched_decks.append({
                "name": deck['name'],
                "url": deck['url'],
                "image": img
            })
        enriched_groups[group_name] = enriched_decks

    return render_template("decks.html", decks=enriched_groups)
