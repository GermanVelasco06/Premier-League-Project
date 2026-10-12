"""
Build a single, Power BI-ready weather table: one row per match, with the
home stadium's weather at kickoff time (venue, temperature, precipitation,
wind speed). It's at the same grain as data/processed/matches.csv (one row
per match_id), so in Power BI it's a straight 1:1 relationship on
`match_id` to the matches table -- no extra modelling needed to explore
weather vs. results/goals.

Needs data/weather/*.csv already downloaded (scripts/download_weather.py).

Usage:
    python scripts/build_weather_table.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.weather import WEATHER_DIR, add_weather_features  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MATCHES_PATH = ROOT / "data" / "processed" / "matches.csv"
OUT_PATH = ROOT / "data" / "processed" / "weather.csv"

OUTPUT_COLUMNS = [
    "match_id", "date", "season", "home_team", "away_team", "venue_name",
    "weather_temp_c", "weather_precip_mm", "weather_wind_kmh",
]


def main() -> int:
    if not MATCHES_PATH.exists():
        print(
            f"ERROR: {MATCHES_PATH} not found. Run scripts/build_dataset.py first.",
            file=sys.stderr,
        )
        return 1
    if not any(WEATHER_DIR.glob("*.csv")):
        print(
            f"ERROR: {WEATHER_DIR} has no weather files. Run scripts/download_weather.py first.",
            file=sys.stderr,
        )
        return 1

    matches = pd.read_csv(MATCHES_PATH, parse_dates=["date"])
    weather = add_weather_features(matches, keep_venue_name=True)
    weather = weather[OUTPUT_COLUMNS]
    weather.to_csv(OUT_PATH, index=False)

    total = len(weather)
    matched = weather["weather_temp_c"].notna().sum()
    print(f"Built weather table: {total} matches, {matched} with weather ({matched / total:.1%})")
    if matched < total:
        missing_teams = (
            weather.loc[weather["weather_temp_c"].isna(), "home_team"].value_counts()
        )
        print(f"  Unmatched rows, by home team:\n{missing_teams}")
    print(f"Saved to {OUT_PATH}")
    print(weather.head())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
