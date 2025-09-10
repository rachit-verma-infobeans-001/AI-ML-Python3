from flask import Blueprint, render_template, abort
from db import get_db_connection

leagues_bp = Blueprint("leagues", __name__, url_prefix="/<sport_slug>/leagues")

@leagues_bp.route("/<int:league_id>")
def league_show(sport_slug, league_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name FROM leagues WHERE id=%s", (league_id,))
        league = cur.fetchone()
        if not league:
            abort(404)

        cur.execute("""
            SELECT g.id, g.start_at, ht.name AS home_team_name, at.name AS away_team_name
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.league_id=%s ORDER BY g.start_at DESC
        """, (league_id,))
        games = cur.fetchall()

        return render_template("leagues/show.html", sport_slug=sport_slug, league=league, games=games)
    finally:
        conn.close()
