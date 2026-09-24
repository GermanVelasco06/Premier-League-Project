"""
Download Premier League club information from API-Football (api-football.com /
API-Sports v3), a richer complement to the football-data.co.uk match data:
club names, crests, home venue, founding year, etc.

Requires an API-Football key in a local .env file (never committed - see
.env.example):

    API_FOOTBALL_KEY=your_key_here

Usage:
    python scripts/download_clubs.py
    python scripts/download_clubs.py --season 2025 --league 39
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://v3.football.api-sports.io/teams"
PREMIER_LEAGUE_ID = 39  # API-Football's id for the English Premier League
CURRENT_SEASON = 2024   # season start year, e.g. 2024 = the 2024-25 season.
                        # Free API-Football plans only allow seasons 2022-2024.
CLUBS_DIR = Path(__file__).resolve().parent.parent / "data" / "clubs"


def fetch_clubs(api_key: str, season: int, league_id: int) -> dict:
    """Call the API-Football /teams endpoint and return the parsed JSON payload."""
    headers = {"x-apisports-key": api_key}
    params = {"league": league_id, "season": season}
    response = requests.get(API_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"API-Football returned errors: {payload['errors']}")
    return payload


def clean_clubs(payload: dict) -> list[dict]:
    """Flatten the API-Football /teams response into simple per-club records."""
    records = []
    for entry in payload.get("response", []):
        team = entry.get("team", {}) or {}
        venue = entry.get("venue", {}) or {}
        records.append(
            {
                "team_id": team.get("id"),
                "name": team.get("name"),
                "code": team.get("code"),
                "country": team.get("country"),
                "founded": team.get("founded"),
                "logo": team.get("logo"),
                "venue_name": venue.get("name"),
                "venue_city": venue.get("city"),
                "venue_capacity": venue.get("capacity"),
            }
        )
    return records


def save_clubs(payload: dict, season: int) -> tuple[Path, Path]:
    """Write the raw JSON response and a cleaned CSV to data/clubs/."""
    CLUBS_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = CLUBS_DIR / f"teams_{season}_raw.json"
    raw_path.write_text(json.dumps(payload, indent=2))

    records = clean_clubs(payload)
    csv_path = CLUBS_DIR / f"teams_{season}.csv"
    fieldnames = list(records[0].keys()) if records else [
        "team_id", "name", "code", "country", "founded", "logo",
        "venue_name", "venue_city", "venue_capacity",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return raw_path, csv_path


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Download PL club info from API-Football")
    parser.add_argument(
        "--season", type=int, default=CURRENT_SEASON,
        help="Season start year (default: 2024; free plans only allow 2022-2024)",
    )
    parser.add_argument(
        "--league", type=int, default=PREMIER_LEAGUE_ID,
        help="API-Football league id (default: 39)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("API_FOOTBALL_KEY")
    if not api_key:
        print(
            "ERROR: API_FOOTBALL_KEY not set. Copy .env.example to .env and add your key.",
            file=sys.stderr,
        )
        return 1

    print(f"Fetching clubs for league {args.league}, season {args.season} ...")
    payload = fetch_clubs(api_key, args.season, args.league)
    records = clean_clubs(payload)

    if not records:
        print("WARNING: no clubs returned - check your league/season parameters.", file=sys.stderr)

    raw_path, csv_path = save_clubs(payload, args.season)
    print(f"  -> raw response saved to {raw_path}")
    print(f"  -> {len(records)} clubs saved to {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
