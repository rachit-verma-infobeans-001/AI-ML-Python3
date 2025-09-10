from flask import Blueprint, render_template
from db import get_db_connection

teams_bp = Blueprint("teams", __name__, url_prefix="/<sport_slug>/teams")

@teams_bp.route("/vs/<vs_slug>")
def teams_vs(sport_slug, vs_slug):
    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        home, away = vs_slug.split("-vs-")
        cur.execute("""
            SELECT g.id, g.start_at,
                   ht.name AS home_team_name, at.name AS away_team_name,
                   g.home_team_ft_score, g.away_team_ft_score
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            JOIN sports s ON g.sport_id = s.id
            WHERE LOWER(REPLACE(ht.name, ' ', '-'))=%s
              AND LOWER(REPLACE(at.name, ' ', '-'))=%s
              AND s.code=%s
            ORDER BY g.start_at DESC
        """, (home, away, sport_slug))
        matchups = cur.fetchall()
        return render_template("teams/vs.html", sport_slug=sport_slug, vs_slug=vs_slug, matchups=matchups)
    finally:
        conn.close()
