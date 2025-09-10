from flask import Blueprint, render_template, request, abort
from datetime import datetime
from db import get_db_connection
from utils import slugify

PAGE_SIZE = 10
games_bp = Blueprint("games", __name__, url_prefix="/<sport_slug>/games")

def fetch_games(conn, sport_id, league_id=None, page=1):
    offset = (page - 1) * PAGE_SIZE
    params = [sport_id]
    league_clause = ""
    if league_id:
        league_clause = " AND g.league_id = %s"
        params.append(league_id)

    sql = f"""
        SELECT g.id, g.start_at,
               ht.name AS home_team_name,
               at.name AS away_team_name,
               v.name AS venue_name,
               l.id AS league_id, l.name AS league_name
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.id
        JOIN teams at ON g.away_team_id = at.id
        JOIN leagues l ON g.league_id = l.id
        JOIN venues v ON g.venue_id = v.id
        WHERE g.sport_id = %s {league_clause}
        ORDER BY g.start_at ASC
        LIMIT %s OFFSET %s
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params + [PAGE_SIZE, offset])
    return cur.fetchall()

@games_bp.route("/")
def games_index(sport_slug):
    page = int(request.args.get("page", 1))
    conn = get_db_connection()
    try:
        # you’d fetch sport_id with a helper (like fetch_sport_id_by_slug)
        # skipping here for brevity
        sport_id = 1  
        games = fetch_games(conn, sport_id, page=page)

        items = []
        for g in games:
            date_obj = g["start_at"] if isinstance(g["start_at"], datetime) else None
            if not date_obj:
                try:
                    date_obj = datetime.fromisoformat(str(g["start_at"]))
                except Exception:
                    date_obj = None
            day_str = date_obj.strftime("%a") if date_obj else ""
            date_str = date_obj.strftime("%b %d") if date_obj else ""
            vs_slug = f"{slugify(g['home_team_name'])}-vs-{slugify(g['away_team_name'])}"

            items.append({
                "id": g["id"],
                "day": day_str.upper(),
                "date": date_str,
                "title": f"{g['home_team_name']} vs {g['away_team_name']}",
                "venue": g["venue_name"],
                "league_id": g["league_id"],
                "league_name": g["league_name"],
                "vs_slug": vs_slug,
            })

        return render_template("games/games.html", sport_slug=sport_slug, items=items)
    finally:
        conn.close()
