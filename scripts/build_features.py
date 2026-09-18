"""
Build the match-level feature table (recent form, home/away strength, and
the expected-goals proxy) from data/processed/matches.csv.

Usage:
    python scripts/build_features.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.features import PROCESSED_DIR, build_feature_table  # noqa: E402


def main() -> int:
    features = build_feature_table()
    print(f"Built feature table with {len(features)} matches and {features.shape[1]} columns")
    print(f"Saved to {PROCESSED_DIR / 'features.csv'}\n")
    cols = [
        "date", "home_team", "away_team",
        "proxy_xg_home", "proxy_xg_away", "home_goals", "away_goals",
    ]
    print(features[cols].head())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
