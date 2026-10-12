"""
Build the match-level feature table (recent form, home/away strength, and
the expected-goals proxy) from data/processed/matches.csv.

Usage:
    python scripts/build_features.py
    python scripts/build_features.py --with-weather   # also needs data/weather/
                                                        # (see scripts/download_weather.py)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.features import PROCESSED_DIR, build_feature_table  # noqa: E402
from src.weather import WEATHER_DIR, add_weather_features  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the match-level feature table")
    parser.add_argument(
        "--with-weather", action="store_true",
        help="Also attach kickoff-time weather (needs data/weather/, see "
             "scripts/download_weather.py)",
    )
    args = parser.parse_args()

    features = build_feature_table()

    if args.with_weather:
        if not any(WEATHER_DIR.glob("*.csv")):
            print(
                f"WARNING: --with-weather was set but {WEATHER_DIR} has no weather "
                "files yet - run scripts/download_weather.py first. Weather columns "
                "will be all-NaN."
            )
        features = add_weather_features(features)
        features.to_csv(PROCESSED_DIR / "features.csv", index=False)

    print(f"Built feature table with {len(features)} matches and {features.shape[1]} columns")
    print(f"Saved to {PROCESSED_DIR / 'features.csv'}\n")
    cols = [
        "date", "home_team", "away_team",
        "proxy_xg_home", "proxy_xg_away", "home_goals", "away_goals",
    ]
    if args.with_weather:
        cols += ["weather_temp_c", "weather_precip_mm", "weather_wind_kmh"]
    print(features[cols].head())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
