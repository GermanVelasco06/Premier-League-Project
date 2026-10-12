import pandas as pd

from src.weather import (
    add_weather_features,
    load_stadium_coords,
    parse_weather_response,
    resolve_stadium,
    stadium_date_ranges,
    venue_slug,
)

COORDS_CSV = (
    "team,venue_name,latitude,longitude,season_from,season_to\n"
    "Arsenal,Emirates Stadium,51.5549,-0.1084,,\n"
    "Everton,Goodison Park,53.4388,-2.9663,,2024-25\n"
    "Everton,Hill Dickinson Stadium,53.4251,-3.0028,2025-26,\n"
)


def write_coords(tmp_path):
    path = tmp_path / "stadium_coords.csv"
    path.write_text(COORDS_CSV)
    return path


def test_venue_slug():
    assert venue_slug("Old Trafford") == "old_trafford"
    assert venue_slug("St James' Park") == "st_james_park"


def test_resolve_stadium_picks_season_appropriate_venue(tmp_path):
    coords = load_stadium_coords(write_coords(tmp_path))

    pre_move = resolve_stadium("Everton", "2023-24", coords)
    post_move = resolve_stadium("Everton", "2025-26", coords)

    assert pre_move["venue_name"] == "Goodison Park"
    assert post_move["venue_name"] == "Hill Dickinson Stadium"


def test_resolve_stadium_unknown_team_returns_none(tmp_path):
    coords = load_stadium_coords(write_coords(tmp_path))
    assert resolve_stadium("Not A Real Team", "2023-24", coords) is None


def test_parse_weather_response_flattens_hourly_block():
    payload = {
        "hourly": {
            "time": ["2023-08-11T14:00", "2023-08-11T15:00"],
            "temperature_2m": [18.2, 17.9],
            "precipitation": [0.0, 0.4],
            "wind_speed_10m": [12.1, 14.0],
        }
    }
    df = parse_weather_response(payload)

    assert len(df) == 2
    assert df.loc[1, "temperature_2m"] == 17.9
    assert df.loc[1, "precipitation"] == 0.4


def test_stadium_date_ranges_respects_season_window(tmp_path):
    coords = load_stadium_coords(write_coords(tmp_path))
    matches = pd.DataFrame(
        {
            "home_team": ["Everton", "Everton", "Everton"],
            "season": ["2023-24", "2024-25", "2025-26"],
            "date": ["2023-09-01", "2024-09-01", "2025-09-01"],
        }
    )

    ranges = stadium_date_ranges(matches, coords)
    ranges = ranges.set_index("venue_name")

    assert ranges.loc["Goodison Park", "start_date"] == "2023-09-01"
    assert ranges.loc["Goodison Park", "end_date"] == "2024-09-01"
    assert ranges.loc["Hill Dickinson Stadium", "start_date"] == "2025-09-01"


def make_matches():
    return pd.DataFrame(
        {
            "match_id": [1, 2],
            "date": ["2023-08-11", "2023-08-12"],
            "kickoff_time": ["20:00", None],
            "season": ["2023-24", "2023-24"],
            "home_team": ["Arsenal", "Arsenal"],
        }
    )


def write_arsenal_weather(tmp_path):
    weather_dir = tmp_path / "weather"
    weather_dir.mkdir()
    weather = pd.DataFrame(
        {
            "time": pd.to_datetime(
                ["2023-08-11T19:00", "2023-08-11T20:00", "2023-08-12T15:00"]
            ),
            "temperature_2m": [17.0, 18.0, 20.0],
            "precipitation": [0.0, 0.1, 0.0],
            "wind_speed_10m": [10.0, 11.0, 8.0],
        }
    )
    weather.to_csv(weather_dir / "emirates_stadium.csv", index=False)
    return weather_dir


def test_add_weather_features_matches_nearest_hour_and_default_kickoff(tmp_path):
    coords_path = write_coords(tmp_path)
    weather_dir = write_arsenal_weather(tmp_path)

    result = add_weather_features(
        make_matches(), weather_dir=weather_dir, coords_path=coords_path
    )

    # Match 1: kickoff 20:00 -> exact hour match.
    assert result.loc[result["match_id"] == 1, "weather_temp_c"].iloc[0] == 18.0
    # Match 2: no kickoff_time -> defaults to 15:00 -> nearest is 15:00 exactly.
    assert result.loc[result["match_id"] == 2, "weather_temp_c"].iloc[0] == 20.0


def test_add_weather_features_missing_weather_file_gives_nan(tmp_path):
    coords_path = write_coords(tmp_path)
    empty_weather_dir = tmp_path / "no_weather_here"
    empty_weather_dir.mkdir()

    result = add_weather_features(
        make_matches(), weather_dir=empty_weather_dir, coords_path=coords_path
    )

    assert result["weather_temp_c"].isna().all()
