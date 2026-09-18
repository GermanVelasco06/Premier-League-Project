# Premier League Match Prediction

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
last 5 completed Premier League seasons (2021-22 to 2025-26). See
[`data/README.md`](data/README.md) for the column reference and how to fetch it.

## Project structure

```
.
├── data/
│   ├── raw/            # Raw season CSVs from football-data.co.uk (gitignored)
│   └── processed/      # Cleaned / merged / feature-engineered dataset (gitignored)
├── notebooks/           # Exploratory analysis and modelling notebooks
├── scripts/
│   └── download_data.py # Fetches the raw season CSVs
├── src/                  # Reusable code (data loading, feature engineering, models)
├── models/               # Saved trained models (gitignored)
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
```

## Status

- [x] Repository and project structure
- [x] Data download script (last 5 EPL seasons)
- [ ] Data cleaning and merging across seasons
- [ ] Feature engineering (form, shot quality / xG proxy, home advantage)
- [ ] Expected goals models (home/away)
- [ ] Match outcome probability model (W/D/L)
- [ ] Model evaluation vs. bookmaker odds

## Tech stack

Python, pandas, NumPy, scikit-learn, XGBoost, matplotlib/seaborn, Jupyter.

## Author

German Velasco Bossa — [GitHub](https://github.com/GermanVelasco19)
