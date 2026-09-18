# Premier League Match Prediction

[![CI](https://github.com/GermanVelasco06/Premier-League-Project/actions/workflows/ci.yml/badge.svg)](https://github.com/GermanVelasco06/Premier-League-Project/actions/workflows/ci.yml)

A personal machine learning project that predicts **expected goals (xG)** for the
home and away team in a Premier League match, then converts those expected goals
into **win / draw / loss probabilities**.

## Goal

1. Build features per match (recent form, attacking/defensive strength, shot
   quality as an xG proxy, home advantage) from the last 5 Premier League seasons.
2. Model expected goals for each side (Poisson / regression style models:
   Ridge Regression, Random Forest, XGBoost).
3. Turn the two expected-goals values into a full match outcome probability
   (Home win / Draw / Away win), e.g. via a Poisson goal-difference model.
4. Evaluate against the bookmakers' implied probabilities as a benchmark.

This supports a longer-term move into machine learning / sports analytics.

## Data

Historical match data (results, shots, cards, and closing odds) comes from
[football-data.co.uk](https://www.football-data.co.uk/englandm.php), covering the
last 5 completed Premier League seasons (2021-22 to 2025-26; 1,900 matches). See
[`data/README.md`](data/README.md) for the column reference and how to fetch it.

## Key findings so far (EDA)

See [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb) for the full analysis.

- **Home advantage is real and consistent**: home teams average 1.60 goals/match
  vs 1.33 away, and matches split 44.2% home win / 23.9% draw / 31.9% away win
  across all 5 seasons.
- **Shots on target correlate with goals scored** (r = 0.59 for the home team),
  supporting shot-based features as an expected-goals proxy in the absence of
  official xG data.
- Goal counts per match are low and discrete (mostly 0-6), which points toward
  **Poisson-style models** for the expected-goals target rather than plain
  linear regression.
- Squads change season to season (promotion/relegation), so features should use
  **rolling recent form** rather than full-history team averages.

## Feature engineering

See [`notebooks/02_feature_validation.ipynb`](notebooks/02_feature_validation.ipynb)
and [`data/README.md`](data/README.md#processed-data) for the full feature
dictionary. Highlights:

- **Recent form** (last 5 matches, any venue) and **venue-specific strength**
  (last 5 home matches for the home team, last 5 away matches for the away
  team) — every rolling stat is shifted so a match's features never include
  its own result (no leakage; see `tests/test_features.py`).
- **`proxy_xg_home` / `proxy_xg_away`**: a Dixon-Coles-style expected-goals
  proxy (attack strength x defence weakness x league average). It's well
  *calibrated* on average (mean 1.61 vs actual 1.60 home goals/match) and
  correctly *ranks* matches by attacking threat, but — as expected for
  single-match football outcomes — isn't a strong point predictor on its own.
  It's built to feed into a model alongside the other features, not to be
  read as a prediction by itself.
- The **current, in-progress season is kept out of training** entirely
  (`data/live/`, fetched separately) — see `data/README.md` for why.

## Project structure

```
.
├── .github/workflows/    # CI: lint (ruff) + tests (pytest) on every push/PR
├── data/
│   ├── raw/                # Raw season CSVs, 5 completed seasons (gitignored)
│   ├── processed/          # Cleaned dataset + feature table (gitignored)
│   └── live/               # Current in-progress season, fetched separately (gitignored)
├── notebooks/
│   ├── 01_eda.ipynb        # Exploratory analysis with visualizations
│   └── 02_feature_validation.ipynb  # Validates the engineered features / xG proxy
├── scripts/
│   ├── download_data.py    # Fetches season CSVs (--output-dir for live data)
│   ├── build_dataset.py    # Cleans + merges seasons into data/processed/matches.csv
│   └── build_features.py   # Builds data/processed/features.csv
├── src/
│   ├── data_loader.py      # Reusable loading/cleaning functions (unit tested)
│   └── features.py         # Feature engineering: form, strength, xG proxy (unit tested)
├── tests/                  # pytest unit tests
├── models/                 # Saved trained models (gitignored)
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download the raw match data
python scripts/download_data.py

# 4. Build the cleaned, merged dataset
python scripts/build_dataset.py

# 5. Build the feature table
python scripts/build_features.py

# 6. Run the tests
pytest -v
```

Then open `notebooks/01_eda.ipynb` and `notebooks/02_feature_validation.ipynb`
to explore the data and the engineered features.

## Status

- [x] Repository and project structure
- [x] Data download script (last 5 EPL seasons)
- [x] Data cleaning, validation and merging (`src/data_loader.py`, unit tested)
- [x] Exploratory data analysis notebook
- [x] CI pipeline (lint + tests on every push)
- [x] Feature engineering (form, venue-specific strength, xG proxy — unit tested)
- [ ] Expected goals models (home/away)
- [ ] Match outcome probability model (W/D/L)
- [ ] Model evaluation vs. bookmaker odds

## Tech stack

Python, pandas, NumPy, scikit-learn, XGBoost, matplotlib/seaborn, Jupyter, pytest, ruff, GitHub Actions.

## Author

German Velasco Bossa — [GitHub](https://github.com/GermanVelasco06)
