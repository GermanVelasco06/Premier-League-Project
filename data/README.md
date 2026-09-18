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

## Processed data
`data/processed/` will hold the cleaned, merged, and feature-engineered dataset
(all 5 seasons combined, rolling form features, shot-based xG proxies, etc.) once
the feature engineering step is built.
