from flask import Blueprint, render_template
from db.db_utils import connect_db, disconnect_db
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/')
def calendar_page():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT data, loja, cor FROM calendar ORDER BY data")
    rows = cur.fetchall()
    cur.close()
    disconnect_db(conn)

    events = []
    for data, loja, cor in rows:
        if not isinstance(data, str):
            data = data.strftime('%Y-%m-%d')
        events.append({
            "title": loja,
            "start": data,
            "className": [f"event-{cor}"]
        })

    return render_template('calendar.html', events_json=events)
