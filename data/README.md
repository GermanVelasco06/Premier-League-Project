# Data

## Source
[football-data.co.uk](https://www.football-data.co.uk/englandm.php) — free historical
match results, match statistics, and betting odds for the English Premier League
(and other leagues), updated regularly since the 2000/01 season.

## How to get the data
Raw CSVs are **not** committed to this repo (see `.gitignore`) — regenerate them with:

```bash
pip install -r requirements.txt
python scripts/download_data.py
```

This downloads the last 5 completed Premier League seasons (2021-22 to 2025-26) into
`data/raw/E0_<season>.csv`. Pass `--seasons` to fetch specific seasons (codes like
`2425` for 2024-25) — see `python scripts/download_data.py --help`.

### The current (in-progress) season is kept separate

`data/raw/` only ever holds **completed** seasons — that's the fixed training set.
The current season (e.g. 2026-27) is fetched into `data/live/` instead:

```bash
python scripts/download_data.py --seasons 2627 --output-dir data/live
```

This is deliberate: mixing a partially-played season into training data would
skew season-level averages, but its played matches are exactly what's needed
to compute a team's *current* form when predicting an upcoming fixture. Live
data is read at prediction time, never used to train the models.

## Column reference (raw files)
Key columns used in this project (full odds columns are also present but not all are used):

| Column | Meaning |
|---|---|
| `Date` | Match date |
| `HomeTeam` / `AwayTeam` | Team names |
| `FTHG` / `FTAG` | Full-time home/away goals (the main target) |
| `FTR` | Full-time result: `H` / `D` / `A` |
| `HTHG` / `HTAG` / `HTR` | Half-time goals and result |
| `HS` / `AS` | Home/away total shots |
| `HST` / `AST` | Home/away shots on target (used as an xG proxy) |
| `HC` / `AC` | Home/away corners |
| `HF` / `AF` | Home/away fouls committed |
| `HY` / `AY` / `HR` / `AR` | Yellow/red cards |
| `B365H` / `B365D` / `B365A` | Bet365 closing odds (home/draw/away) — useful as a benchmark for our own probabilities |

Full column glossary: https://www.football-data.co.uk/notes.txt

## Club information (API-Football)

`data/clubs/` holds club-level info (crest, home venue, founding year, etc.)
from [API-Football](https://www.api-football.com/) (v3, api-sports.io) — a
richer complement to football-data.co.uk, which only has match results.

Requires a free API-Football key. Copy `.env.example` to `.env` in the project
root and set `API_FOOTBALL_KEY=your_key` (`.env` is gitignored — your key is
never committed). Then:

```bash
python scripts/download_clubs.py
python scripts/download_clubs.py --season 2025   # a different season
```

This saves the raw API response (`data/clubs/teams_<season>_raw.json`) and a
cleaned CSV (`data/clubs/teams_<season>.csv`) with one row per club: `team_id`,
`name`, `code`, `country`, `founded`, `logo`, `venue_name`, `venue_city`,
`venue_capacity`. Both are gitignored, same as the match data.

## Processed data

`data/processed/matches.csv` — the 5 seasons cleaned and merged into one table
(built by `scripts/build_dataset.py`). One row per match.

`data/processed/features.csv` — the match-level feature table (built by
`scripts/build_features.py`, from `src/features.py`). Adds, for every match,
*pre-match* features for the home and away team:

| Column group | Meaning |
|---|---|
| `{home,away}_form_goals_for/against` | Rolling average goals scored/conceded over the last 5 matches (any venue) |
| `{home,away}_form_shots_for` / `_shots_target_for` | Rolling average shots / shots on target over the last 5 matches |
| `{home,away}_form_points` | Rolling average points (3/1/0) over the last 5 matches — overall form |
| `{home,away}_venue_goals_for/against` | Rolling average goals scored/conceded over the last 5 matches **at that venue only** (home matches for the home team, away matches for the away team) — captures home-specific / away-specific strength |
| `proxy_xg_home` / `proxy_xg_away` | Expected-goals proxy: `attack strength x defence weakness x league average goals` (Dixon-Coles style), built from the venue-specific rolling stats above |

All rolling stats are computed using only matches *before* the one they're
attached to (shifted by one) — see `tests/test_features.py::test_rolling_form_has_no_leakage`.
A team's first ~5 matches in the dataset have no history yet; those rows are
imputed with the league-wide median rather than dropped.

See `notebooks/02_feature_validation.ipynb` for validation of the expected-goals
proxy (calibration and error vs. a naive baseline).
