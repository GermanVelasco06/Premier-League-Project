"""
Download historical hourly weather for every Premier League stadium in
data/clubs/stadium_coords.csv, from Open-Meteo's free historical weather API
(https://open-meteo.com/en/docs/historical-weather-api) -- no API key
required.

Open-Meteo re-serves ERA5, the climate reanalysis produced by
Copernicus/ECMWF (not a government feed, but the standard reference dataset
in climate research). Cite it as:

    ERA5 reanalysis (Copernicus/ECMWF), accessed via Open-Meteo

For each stadium, one API call covers its whole relevant date range -- the
home matches actually played there, from data/processed/matches.csv, bounded
by the season_from/season_to window in stadium_coords.csv (this matters for
Everton, who moved from Goodison Park to the Hill Dickinson Stadium for the
2025-26 season).

Usage:
    python scripts/download_data.py     # match data first (if not done yet)
    python scripts/build_dataset.py     # -> data/processed/matches.csv
    python scripts/download_weather.py  # this script -> data/weather/*.csv
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.weather import (  # noqa: E402
    HOURLY_VARS,
    STADIUM_COORDS_PATH,
    WEATHER_DIR,
    load_stadium_coords,
    parse_weather_response,
    stadium_date_ranges,
    venue_slug,
)

MATCHES_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "matches.csv"
API_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEZONE = "Europe/London"
REQUEST_DELAY_S = 1.2  # be polite to the free API


def fetch_hourly_weather(
    latitude: float, longitude: float, start_date: str, end_date: str
) -> dict:
    """Call Open-Meteo's historical weather API and return the parsed JSON payload."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": TIMEZONE,
    }
    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if "hourly" not in payload:
        raise RuntimeError(f"Open-Meteo returned an unexpected response: {payload}")
    return payload


def main() -> int:
    if not MATCHES_PATH.exists():
        print(
            f"ERROR: {MATCHES_PATH} not found. Run scripts/build_dataset.py first.",
            file=sys.stderr,
        )
        return 1

    matches = pd.read_csv(MATCHES_PATH)
    coords = load_stadium_coords(STADIUM_COORDS_PATH)
    stadiums = stadium_date_ranges(matches, coords).reset_index(drop=True)

    WEATHER_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Fetching weather for {len(stadiums)} stadiums ...")
    for i, stadium in stadiums.iterrows():
        slug = venue_slug(stadium["venue_name"])
        out_path = WEATHER_DIR / f"{slug}.csv"
        print(
            f"  [{i + 1}/{len(stadiums)}] {stadium['team']} - {stadium['venue_name']} "
            f"({stadium['start_date']} to {stadium['end_date']}) ..."
        )
        payload = fetch_hourly_weather(
            stadium["latitude"], stadium["longitude"],
            stadium["start_date"], stadium["end_date"],
        )
        weather = parse_weather_response(payload)
        weather.to_csv(out_path, index=False)
        print(f"    -> {len(weather)} hourly rows saved to {out_path}")
        time.sleep(REQUEST_DELAY_S)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
