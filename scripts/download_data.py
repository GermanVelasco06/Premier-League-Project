"""
Download historical Premier League match data from football-data.co.uk
for the last 5 completed seasons (2021-22 through 2025-26).

Usage:
    python scripts/download_data.py
    python scripts/download_data.py --seasons 2223 2324 2425

Each season is saved as data/raw/E0_<start>-<end>.csv, e.g. data/raw/E0_2021-22.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/E0.csv"
# football-data.co.uk season codes: "2122" = 2021-22, ... "2526" = 2025-26
DEFAULT_SEASONS = ["2122", "2223", "2324", "2425", "2526"]
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
LIVE_DIR = Path(__file__).resolve().parent.parent / "data" / "live"


def season_label(code: str) -> str:
    """'2425' -> '2024-25'"""
    return f"20{code[:2]}-{code[2:]}"


def download_season(session: requests.Session, season: str, out_dir: Path) -> Path:
    url = BASE_URL.format(season=season)
    label = season_label(season)
    dest = out_dir / f"E0_{label}.csv"

    print(f"Downloading {label} season from {url} ...")
    response = session.get(url, timeout=30)
    response.raise_for_status()

    dest.write_bytes(response.content)
    print(f"  -> saved to {dest} ({len(response.content):,} bytes)")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download historical Premier League match data (football-data.co.uk)"
    )
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=DEFAULT_SEASONS,
        help=(
            "football-data.co.uk season codes, e.g. 2425 for 2024-25 "
            "(default: last 5 completed seasons, 2021-22 to 2025-26)"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(RAW_DIR),
        help=(
            "Where to save the CSVs. Use the default (data/raw) for the 5 completed "
            "training seasons, or data/live for the current in-progress season "
            "(kept separate so it never leaks into the training dataset)."
        ),
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; PL-Prediction-Project/1.0)"})

    failed: list[str] = []
    for season in args.seasons:
        try:
            download_season(session, season, out_dir)
        except requests.RequestException as exc:
            print(f"  ERROR downloading {season_label(season)}: {exc}", file=sys.stderr)
            failed.append(season)

    if failed:
        print(f"\n{len(failed)} season(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1

    print(f"\nDone. {len(args.seasons)} season(s) downloaded to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
