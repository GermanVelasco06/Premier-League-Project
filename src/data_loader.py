"""
Data loading and cleaning utilities for the Premier League match dataset.

Reads the raw football-data.co.uk season CSVs (see scripts/download_data.py),
cleans and standardises them, and merges all seasons into a single tidy
DataFrame ready for feature engineering.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

# Raw football-data.co.uk column -> tidy column name. Only columns present in
# COLUMNS are kept; any other columns in the raw file (e.g. extra betting
# markets) are dropped.
COLUMNS: dict[str, str] = {
    "Date": "date",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "result",
    "HTHG": "home_goals_ht",
    "HTAG": "away_goals_ht",
    "HTR": "result_ht",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_target",
    "AST": "away_shots_target",
    "HC": "home_corners",
    "AC": "away_corners",
    "HF": "home_fouls",
    "AF": "away_fouls",
    "HY": "home_yellow",
    "AY": "away_yellow",
    "HR": "home_red",
    "AR": "away_red",
    "B365H": "odds_home",
    "B365D": "odds_draw",
    "B365A": "odds_away",
}

REQUIRED_COLUMNS = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]


def season_from_filename(path: Path) -> str:
    """Extract the season label from a raw file name, e.g. 'E0_2023-24.csv' -> '2023-24'."""
    stem = path.stem  # "E0_2023-24"
    return stem.split("_", 1)[1] if "_" in stem else stem


def load_season_file(path: Path) -> pd.DataFrame:
    """Load and lightly clean a single raw football-data.co.uk season CSV.

    Raises:
        ValueError: if the file is missing one of the columns every match
            record needs (home/away team, date, full-time score/result).
    """
    df = pd.read_csv(path, encoding="utf-8-sig")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")

    keep = [c for c in COLUMNS if c in df.columns]
    df = df[keep].rename(columns=COLUMNS)

    # Drop any rows without a final score (postponed / not-yet-played fixtures).
    df = df.dropna(subset=["home_goals", "away_goals"]).copy()

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)
    df["season"] = season_from_filename(path)

    return df.reset_index(drop=True)


def load_all_seasons(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load and concatenate every ``E0_*.csv`` season file found in ``raw_dir``.

    Raises:
        FileNotFoundError: if no season files are found (i.e.
            ``scripts/download_data.py`` hasn't been run yet).
    """
    files = sorted(Path(raw_dir).glob("E0_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No season files found in {raw_dir}. Run scripts/download_data.py first."
        )

    seasons = [load_season_file(f) for f in files]
    matches = pd.concat(seasons, ignore_index=True)
    matches = matches.sort_values(["date", "home_team"]).reset_index(drop=True)
    matches.insert(0, "match_id", range(1, len(matches) + 1))
    return matches


def build_processed_dataset(
    raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR
) -> pd.DataFrame:
    """Load all seasons, clean them, and write the combined dataset to disk."""
    matches = load_all_seasons(raw_dir)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    matches.to_csv(processed_dir / "matches.csv", index=False)
    return matches
