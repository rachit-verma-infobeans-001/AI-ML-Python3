from flask import Flask, render_template, request, abort
from datetime import datetime
from db import get_db_connection
import re
import ipdb

app = Flask(__name__)

PAGE_SIZE = 10


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip('-')


def fetch_sport_id_by_slug(conn, sport_slug):
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM sports WHERE code = %s LIMIT 1", (sport_slug,))
        row = cur.fetchone()
        if row:
            return row['id']
    except Exception:
        pass
    cur.execute("SELECT id FROM sports WHERE LOWER(name)=LOWER(%s) LIMIT 1", (sport_slug,))
    row = cur.fetchone()
    return row['id'] if row else None


def fetch_leagues_for_sport(conn, sport_id):
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT DISTINCT l.id, l.name
        FROM leagues l
        JOIN games g ON g.league_id = l.id
        WHERE g.sport_id = %s
        ORDER BY l.name ASC
        """,
        (sport_id,)
    )
    return cur.fetchall()


def fetch_games(conn, sport_id, league_id=None, page=1):
    offset = (page - 1) * PAGE_SIZE
    params = [sport_id]
    league_clause = ""
    if league_id:
        league_clause = " AND g.league_id = %s"
        params.append(league_id)

    count_sql = (
        "SELECT COUNT(*) AS cnt FROM games g WHERE g.sport_id = %s" + league_clause
    )

    sql = (
        """
        SELECT g.id, g.start_at,
               ht.name AS home_team_name,
               at.name AS away_team_name,
               v.name AS venue_name,
               l.id   AS league_id,
               l.name AS league_name
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.id
        JOIN teams at ON g.away_team_id = at.id
        JOIN leagues l ON g.league_id = l.id
        JOIN venues v ON g.venue_id = v.id
        WHERE g.sport_id = %s
        """ + league_clause + " ORDER BY g.start_at ASC LIMIT %s OFFSET %s"
    )

    cur = conn.cursor(dictionary=True)
    # total count
    cur.execute(count_sql, params)
    total = cur.fetchone()['cnt']

    # list
    cur.execute(sql, params + [PAGE_SIZE, offset])
    rows = cur.fetchall()
    return rows, total


@app.route('/<sport_slug>/games/')
def games_index(sport_slug):
    page = int(request.args.get('page', 1))
    league_id = request.args.get('league_id')

    conn = get_db_connection()
    try:
        sport_id = fetch_sport_id_by_slug(conn, sport_slug)
        if not sport_id:
            abort(404)

        leagues = fetch_leagues_for_sport(conn, sport_id)
        league_id_int = int(league_id) if league_id else None

        games, total = fetch_games(conn, sport_id, league_id_int, page)
        total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

        items = []
        for g in games:
            date_obj = g['start_at'] if isinstance(g['start_at'], datetime) else None
            if not date_obj:
                try:
                    date_obj = datetime.fromisoformat(str(g['start_at']))
                except Exception:
                    date_obj = None
            day_str = date_obj.strftime('%a') if date_obj else ''
            date_str = date_obj.strftime('%b %d') if date_obj else ''

            game_title = f"{g['home_team_name']} vs {g['away_team_name']}"
            vs_slug = f"{slugify(g['home_team_name'])}-vs-{slugify(g['away_team_name'])}"

            items.append({
                'id': g['id'],
                'day': day_str.upper(),
                'date': date_str,
                'title': game_title,
                'venue': g['venue_name'],
                'league_id': g['league_id'],
                'league_name': g['league_name'],
                'vs_slug': vs_slug,
            })

        return render_template(
            'games/games.html',
            sport_slug=sport_slug,
            leagues=leagues,
            selected_league_id=league_id_int,
            items=items,
            page=page,
            total_pages=total_pages,
        )
    finally:
        conn.close()

def fetch_game_details(conn, game_id):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT g.id, g.start_at, g.home_team_ft_score, g.away_team_ft_score,
               ht.name AS home_team_name,
               at.name AS away_team_name,
               l.id AS league_id, l.name AS league_name,
               v.name AS venue_name
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.id
        JOIN teams at ON g.away_team_id = at.id
        JOIN leagues l ON g.league_id = l.id
        JOIN venues v ON g.venue_id = v.id
        WHERE g.id = %s
    """, (game_id,))
    return cur.fetchone()

@app.route('/<sport_slug>/games/<int:game_id>')
def game_show(sport_slug, game_id):
    conn = get_db_connection()
    try:
        game = fetch_game_details(conn, game_id)
        if not game:
            abort(404)
        return render_template("games/show.html", sport_slug=sport_slug, game=game)
    finally:
        conn.close()




#LEAGUES

def fetch_league_details(conn, league_id):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name FROM leagues WHERE id=%s", (league_id,))
    return cur.fetchone()

def fetch_games_for_league(conn, league_id):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT g.id, g.start_at,
               ht.name AS home_team_name,
               at.name AS away_team_name
        FROM games g
        JOIN teams ht ON g.home_team_id = ht.id
        JOIN teams at ON g.away_team_id = at.id
        WHERE g.league_id=%s
        ORDER BY g.start_at DESC
    """, (league_id,))
    return cur.fetchall()

@app.route('/<sport_slug>/leagues/<int:league_id>')
def league_show(sport_slug, league_id):
    conn = get_db_connection()
    try:
        league = fetch_league_details(conn, league_id)
        if not league:
            abort(404)
        games = fetch_games_for_league(conn, league_id)
        return render_template("leagues/show.html", sport_slug=sport_slug, league=league, games=games)
    finally:
        conn.close()



#VS PAGE

def fetch_matchups(conn, sport_slug, vs_slug):
    home, away = vs_slug.split("-vs-")
    cur = conn.cursor(dictionary=True)
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
    return cur.fetchall()

@app.route('/<sport_slug>/teams/vs/<vs_slug>')
def teams_vs(sport_slug, vs_slug):
    conn = get_db_connection()
    try:
        matchups = fetch_matchups(conn, sport_slug, vs_slug)
        return render_template("teams/vs.html", sport_slug=sport_slug, vs_slug=vs_slug, matchups=matchups)
    finally:
        conn.close()



if __name__ == '__main__':
    app.run(debug=True)





# from flask import Flask
# from controllers.games_controller import games_bp
# from controllers.leagues_controller import leagues_bp
# from controllers.teams_controller import teams_bp

# app = Flask(__name__)

# # register controllers
# app.register_blueprint(games_bp)
# app.register_blueprint(leagues_bp)
# app.register_blueprint(teams_bp)

# if __name__ == "__main__":
#     app.run(debug=True)

