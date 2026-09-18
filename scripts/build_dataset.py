"""
Build the unified, cleaned Premier League match dataset from the raw
per-season CSVs downloaded by scripts/download_data.py.

Usage:
    python scripts/build_dataset.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import PROCESSED_DIR, build_processed_dataset  # noqa: E402


def main() -> int:
    matches = build_processed_dataset()
    print(f"Built dataset with {len(matches)} matches across {matches['season'].nunique()} seasons")
    print(f"Saved to {PROCESSED_DIR / 'matches.csv'}\n")
    print(matches.head())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
