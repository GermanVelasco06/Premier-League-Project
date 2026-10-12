"""
Weather features: merge per-stadium hourly weather onto match-level data by
kickoff date and time.

The weather itself comes from Open-Meteo's free historical weather API (no
key required) -- see scripts/download_weather.py. Open-Meteo isn't the
original data provider; it re-serves ERA5, the climate reanalysis produced
by Copernicus/ECMWF, which is the standard reference dataset in climate
research. Cite it as:

    ERA5 reanalysis (Copernicus/ECMWF), accessed via Open-Meteo
    (https://open-meteo.com/en/docs/historical-weather-api)
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
STADIUM_COORDS_PATH = ROOT / "data" / "clubs" / "stadium_coords.csv"
WEATHER_DIR = ROOT / "data" / "weather"

HOURLY_VARS = ["temperature_2m", "precipitation", "wind_speed_10m"]
WEATHER_RENAME = {
    "temperature_2m": "weather_temp_c",
    "precipitation": "weather_precip_mm",
    "wind_speed_10m": "weather_wind_kmh",
}
DEFAULT_KICKOFF = "15:00"  # used when a match has no recorded kickoff time
MERGE_TOLERANCE = pd.Timedelta("3h")


def venue_slug(venue_name: str) -> str:
    """Filesystem-safe name for a venue, e.g. 'Old Trafford' -> 'old_trafford'."""
    return re.sub(r"[^a-z0-9]+", "_", venue_name.lower()).strip("_")


def load_stadium_coords(path: Path = STADIUM_COORDS_PATH) -> pd.DataFrame:
    """Load the hand-built stadium reference table (team, venue, lat/lon, and
    the season range a venue applies for). Only Everton has more than one
    row, after their 2025-26 move to the Hill Dickinson Stadium."""
    coords = pd.read_csv(path, dtype={"season_from": str, "season_to": str})
    return coords.fillna({"season_from": "", "season_to": ""})


def resolve_stadium(team: str, season: str, coords: pd.DataFrame) -> pd.Series | None:
    """Return the stadium row for `team` that applies in `season`, or None
    if `team` isn't in the reference table."""
    for _, row in coords[coords["team"] == team].iterrows():
        if row["season_from"] and season < row["season_from"]:
            continue
        if row["season_to"] and season > row["season_to"]:
            continue
        return row
    return None


def stadium_date_ranges(matches: pd.DataFrame, coords: pd.DataFrame) -> pd.DataFrame:
    """For each stadium row, the [start, end] date of home matches actually
    played there (respecting season_from/season_to) -- what
    scripts/download_weather.py needs to know how much history to fetch."""
    matches = matches.copy()
    matches["date"] = pd.to_datetime(matches["date"])

    rows = []
    for _, stadium in coords.iterrows():
        team_matches = matches[matches["home_team"] == stadium["team"]]
        if stadium["season_from"]:
            team_matches = team_matches[team_matches["season"] >= stadium["season_from"]]
        if stadium["season_to"]:
            team_matches = team_matches[team_matches["season"] <= stadium["season_to"]]
        if team_matches.empty:
            continue
        rows.append(
            {
                "team": stadium["team"],
                "venue_name": stadium["venue_name"],
                "latitude": stadium["latitude"],
                "longitude": stadium["longitude"],
                "start_date": team_matches["date"].min().date().isoformat(),
                "end_date": team_matches["date"].max().date().isoformat(),
            }
        )
    return pd.DataFrame(rows)


def parse_weather_response(payload: dict) -> pd.DataFrame:
    """Flatten an Open-Meteo historical-weather API response's 'hourly'
    block into a tidy per-hour DataFrame."""
    hourly = payload["hourly"]
    df = pd.DataFrame({"time": pd.to_datetime(hourly["time"])})
    for var in HOURLY_VARS:
        df[var] = hourly.get(var)
    return df


def _load_weather_for_venue(venue_name: str, weather_dir: Path) -> pd.DataFrame | None:
    path = Path(weather_dir) / f"{venue_slug(venue_name)}.csv"
    if not path.exists():
        return None
    weather = pd.read_csv(path, parse_dates=["time"])
    return weather.sort_values("time").reset_index(drop=True)


def add_weather_features(
    matches: pd.DataFrame,
    weather_dir: Path = WEATHER_DIR,
    coords_path: Path = STADIUM_COORDS_PATH,
    default_kickoff: str = DEFAULT_KICKOFF,
) -> pd.DataFrame:
    """Attach kickoff-time weather (temperature, precipitation, wind speed)
    to every match, matched by the home team's stadium, date, and kickoff
    time (falling back to `default_kickoff` when a match has no recorded
    time -- true for older football-data.co.uk seasons).

    A match whose stadium has no downloaded weather file, or whose kickoff
    falls more than 3 hours from the nearest hourly reading, gets NaN
    weather columns rather than a silently wrong value.
    """
    matches = matches.copy()
    coords = load_stadium_coords(coords_path)
    weather_cols = list(WEATHER_RENAME.values())

    if "kickoff_time" in matches.columns:
        kickoff = matches["kickoff_time"].fillna(default_kickoff)
    else:
        kickoff = pd.Series(default_kickoff, index=matches.index)
    date_only = pd.to_datetime(matches["date"]).dt.strftime("%Y-%m-%d")
    matches["_kickoff_dt"] = pd.to_datetime(date_only + " " + kickoff.astype(str), errors="coerce")
    matches["_venue_name"] = matches.apply(
        lambda r: _venue_name_for(r["home_team"], r["season"], coords), axis=1
    )

    parts = []
    for venue_name, group in matches.groupby("_venue_name", dropna=False):
        weather = _load_weather_for_venue(venue_name, weather_dir) if venue_name else None
        if weather is None:
            out = group.copy()
            for col in weather_cols:
                out[col] = pd.NA
            parts.append(out)
            continue
        merged = pd.merge_asof(
            group.sort_values("_kickoff_dt"),
            weather.rename(columns=WEATHER_RENAME),
            left_on="_kickoff_dt", right_on="time",
            direction="nearest", tolerance=MERGE_TOLERANCE,
        )
        parts.append(merged)

    result = pd.concat(parts, ignore_index=True)
    sort_col = "match_id" if "match_id" in result.columns else "_kickoff_dt"
    result = result.sort_values(sort_col).reset_index(drop=True)
    return result.drop(columns=["_kickoff_dt", "_venue_name", "time"], errors="ignore")


def _venue_name_for(team: str, season: str, coords: pd.DataFrame) -> str | None:
    stadium = resolve_stadium(team, season, coords)
    return stadium["venue_name"] if stadium is not None else None
