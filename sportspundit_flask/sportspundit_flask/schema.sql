DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS h2h_stats;
DROP TABLE IF EXISTS match_scorecards;

CREATE TABLE matches (
    id INTEGER PRIMARY KEY,
    team1 TEXT,
    team2 TEXT,
    date TEXT
);

INSERT INTO matches (team1, team2, date) VALUES
('Australia', 'West Indies', '2024-02-15'),
('India', 'England', '2024-02-20');

CREATE TABLE h2h_stats (
    match_id INTEGER,
    stat TEXT,
    team1_value TEXT,
    team2_value TEXT
);

INSERT INTO h2h_stats VALUES
(1, 'Matches Played', '3', '3'),
(1, 'Matches Won', '2', '1'),
(1, 'League Rank', '2', '5'),
(1, 'Average Score', '209', '212'),
(1, 'Highest Score', '241', '220'),
(1, 'Best Bowling Figures', '3/26', '3/42'),
(1, 'Six-Month Win Rate', 'No Wins', 'No Wins'),
(1, 'Overall Win Rate', '70%', '55%');

CREATE TABLE match_scorecards (
    match_id INTEGER,
    date TEXT,
    venue TEXT,
    winner TEXT,
    result TEXT,
    team1_runs TEXT,
    team2_runs TEXT
);

INSERT INTO match_scorecards VALUES
(1, 'Feb 09, 2024', 'Bellerive Oval', 'Australia National Cricket Team', 'AUS won by 11 runs', '213-7', '202-8'),
(1, 'Feb 11, 2024', 'Adelaide Oval', 'Australia National Cricket Team', 'AUS won by 34 runs', '241-4', '207-9'),
(1, 'Feb 13, 2024', 'Perth Stadium', 'West Indies National Cricket Team', 'WES won by 37 runs', '183-5', '220-6');
