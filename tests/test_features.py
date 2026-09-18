import pandas as pd

from src.features import add_rolling_form, build_match_features, to_team_matches


def make_matches() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "match_id": [1, 2, 3],
            "date": pd.to_datetime(["2023-08-01", "2023-08-08", "2023-08-15"]),
            "season": ["2023-24"] * 3,
            "home_team": ["Arsenal", "Chelsea", "Arsenal"],
            "away_team": ["Chelsea", "Arsenal", "Chelsea"],
            "home_goals": [2, 1, 3],
            "away_goals": [0, 1, 2],
            "result": ["H", "D", "H"],
            "home_shots": [10, 8, 12],
            "away_shots": [5, 9, 7],
            "home_shots_target": [6, 4, 8],
            "away_shots_target": [2, 5, 3],
        }
    )


def test_to_team_matches_shape_and_points():
    team_matches = to_team_matches(make_matches())

    # 3 matches x 2 teams per match = 6 rows
    assert len(team_matches) == 6

    arsenal = team_matches[team_matches["team"] == "Arsenal"].sort_values("date")
    # match 1: Arsenal home, won 2-0 -> 3 points, scored 2
    assert arsenal.iloc[0]["points"] == 3
    assert arsenal.iloc[0]["goals_for"] == 2
    # match 2: Arsenal away, drew 1-1 -> 1 point, scored 1
    assert arsenal.iloc[1]["points"] == 1
    assert arsenal.iloc[1]["goals_for"] == 1


def test_rolling_form_has_no_leakage():
    team_matches = to_team_matches(make_matches())
    formed = add_rolling_form(team_matches, window=5)

    arsenal = formed[formed["team"] == "Arsenal"].sort_values("date").reset_index(drop=True)

    # 1st ever match for Arsenal in this dataset: no history yet -> NaN
    assert pd.isna(arsenal.loc[0, "form_goals_for"])

    # 2nd match: form must come ONLY from match 1 (scored 2), not from the
    # 1 goal Arsenal scores in this same (2nd) match
    assert arsenal.loc[1, "form_goals_for"] == 2

    # 3rd match: form is the average of matches 1 and 2 (2 and 1), NOT
    # including the 3 goals Arsenal scores in this (3rd) match itself
    assert arsenal.loc[2, "form_goals_for"] == 1.5


def test_build_match_features_no_nans_and_expected_columns():
    features = build_match_features(make_matches())

    assert len(features) == 3
    expected = {
        "home_form_goals_for",
        "away_form_goals_for",
        "home_venue_goals_for",
        "away_venue_goals_for",
        "proxy_xg_home",
        "proxy_xg_away",
    }
    assert expected.issubset(features.columns)

    prefixes = ("home_form", "away_form", "proxy_xg")
    feature_cols = [c for c in features.columns if c.startswith(prefixes)]
    assert not features[feature_cols].isna().any().any()


def test_proxy_xg_is_positive():
    features = build_match_features(make_matches())
    assert (features["proxy_xg_home"] >= 0).all()
    assert (features["proxy_xg_away"] >= 0).all()
