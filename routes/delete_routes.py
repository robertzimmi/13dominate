from flask import Blueprint, render_template, request, redirect, url_for, flash
from db.db_utils import connect_db
from list_adm.topheroes_pop import get_available_dates
from google_drive.google_drive_client import archive_drive_folder_by_date  # <- novo import

delete_bp = Blueprint('delete_bp', __name__)

@delete_bp.route("/admin/delete-day", methods=["GET", "POST"])
def delete_day():
    if request.method == "POST":
        data_str = request.form.get("data")
        if not data_str:
            flash("Selecione uma data para deletar.", "warning")
            return redirect(url_for('delete_bp.delete_day'))

        conn = None
        try:
            conn = connect_db()
            cur = conn.cursor()

            cur.execute("SELECT id FROM eventos WHERE data = %s", (data_str,))
            eventos_ids = [row[0] for row in cur.fetchall()]

            if not eventos_ids:
                flash(f"Nenhum evento encontrado na data {data_str}.", "info")
                return redirect(url_for('delete_bp.delete_day'))

            print(f"\n=== INICIANDO ARQUIVAMENTO PARA {data_str} ===")

            for eid in eventos_ids:
                print(f"➡️ Deletando dados do evento ID {eid}...")
                cur.execute("DELETE FROM standings WHERE event_id = %s", (eid,))
                cur.execute("DELETE FROM pairings WHERE event_id = %s", (eid,))
                cur.execute("DELETE FROM heroes WHERE event_id = %s", (eid,))
                cur.execute("DELETE FROM calendar WHERE event_id = %s", (eid,))
                cur.execute("DELETE FROM eventos WHERE id = %s", (eid,))

            print(f"📦 Movendo pastas para 'DELETADO': {data_str}")
            archive_drive_folder_by_date(data_str)  # ✅ Aqui em vez de delete

            cur.execute("REFRESH MATERIALIZED VIEW mv_pairings_aggregated;")
            cur.execute("REFRESH MATERIALIZED VIEW v_hero_stats_mat;")
            print("[INFO] Materialized views atualizadas.")
            conn.commit()
            flash(f"Data {data_str} deletada do banco e arquivada no Drive!", "success")

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ ERRO: {e}")
            flash(f"Erro ao processar deleção/arquivamento: {e}", "danger")

        finally:
            if conn:
                conn.close()

        return redirect(url_for('delete_bp.delete_day'))

    datas = get_available_dates()
    return render_template("delete_day.html", datas=datas)