"""
Feature engineering for the Premier League expected-goals model.

Turns the match-level dataset (data/processed/matches.csv) into a match-level
feature table: for every match, a set of *pre-match* features for the home
and away team (recent form, attack/defence strength split by venue, and a
shot-based expected-goals proxy), computed using only information available
before kick-off.

Avoiding leakage: every rolling statistic is shifted by one match per team
before being attached to a fixture, so a team's features for match N never
include match N's own result. See tests/test_features.py::test_rolling_form_has_no_leakage.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

FORM_WINDOW = 5    # matches, any venue - "recent form"
VENUE_WINDOW = 5   # matches, home-only / away-only - "home/away strength"

HOME_RENAME = {
    "form_goals_for": "home_form_goals_for",
    "form_goals_against": "home_form_goals_against",
    "form_shots_for": "home_form_shots_for",
    "form_shots_target_for": "home_form_shots_target_for",
    "form_points": "home_form_points",
    "home_goals_for": "home_venue_goals_for",
    "home_goals_against": "home_venue_goals_against",
}
AWAY_RENAME = {
    "form_goals_for": "away_form_goals_for",
    "form_goals_against": "away_form_goals_against",
    "form_shots_for": "away_form_shots_for",
    "form_shots_target_for": "away_form_shots_target_for",
    "form_points": "away_form_points",
    "away_goals_for": "away_venue_goals_for",
    "away_goals_against": "away_venue_goals_against",
}


def to_team_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Reshape one row per match into two rows per match (one per team).

    Each row is that team's own perspective on the match: goals for/against,
    shots for, whether it was a home match, and points earned (3/1/0).
    """

    def side(home: bool) -> pd.DataFrame:
        team_col = "home_team" if home else "away_team"
        opp_col = "away_team" if home else "home_team"
        goals_for_col = "home_goals" if home else "away_goals"
        goals_against_col = "away_goals" if home else "home_goals"
        shots_for_col = "home_shots" if home else "away_shots"
        shots_target_col = "home_shots_target" if home else "away_shots_target"

        out = pd.DataFrame(
            {
                "match_id": matches["match_id"],
                "date": matches["date"],
                "season": matches["season"],
                "team": matches[team_col],
                "opponent": matches[opp_col],
                "is_home": home,
                "goals_for": matches[goals_for_col],
                "goals_against": matches[goals_against_col],
                "shots_for": matches[shots_for_col],
                "shots_target_for": matches[shots_target_col],
            }
        )
        points_map = {"H": 3, "D": 1, "A": 0} if home else {"A": 3, "D": 1, "H": 0}
        out["points"] = matches["result"].map(points_map)
        return out

    team_matches = pd.concat([side(True), side(False)], ignore_index=True)
    return team_matches.sort_values(["team", "date"]).reset_index(drop=True)


def _pre_match_rolling(group: pd.DataFrame, cols: list[str], window: int) -> pd.DataFrame:
    """Rolling mean of `cols` over the previous `window` matches, shifted by
    one so the current match's own result is never included."""
    return group[cols].shift(1).rolling(window, min_periods=1).mean()


def add_rolling_form(team_matches: pd.DataFrame, window: int = FORM_WINDOW) -> pd.DataFrame:
    """Add overall recent-form columns (any venue), pre-match, per team."""
    stat_cols = ["goals_for", "goals_against", "shots_for", "shots_target_for", "points"]
    rolled = team_matches.groupby("team", group_keys=False)[stat_cols + ["team"]].apply(
        lambda g: _pre_match_rolling(g, stat_cols, window)
    )
    rolled = rolled.add_prefix("form_")
    return pd.concat([team_matches, rolled], axis=1)


def add_venue_strength(team_matches: pd.DataFrame, window: int = VENUE_WINDOW) -> pd.DataFrame:
    """Add venue-specific (home-only / away-only) attack & defence rolling stats.

    A home row gets its rolling average goals for/against *from previous home
    matches only*; an away row gets it from previous away matches only. This
    is what lets the model separate "strong at home" from "strong on the
    road" for the same team.
    """
    stat_cols = ["goals_for", "goals_against"]
    parts = []
    for is_home, group in team_matches.groupby("is_home"):
        prefix = "home_" if is_home else "away_"
        rolled = group.groupby("team", group_keys=False)[stat_cols + ["team"]].apply(
            lambda g: _pre_match_rolling(g, stat_cols, window)
        )
        rolled = rolled.add_prefix(prefix)
        parts.append(pd.concat([group, rolled], axis=1))
    return pd.concat(parts).sort_index()


def build_match_features(matches: pd.DataFrame) -> pd.DataFrame:
    """Build the full match-level feature table from a cleaned matches DataFrame
    (as produced by src.data_loader.load_all_seasons)."""
    team_matches = to_team_matches(matches)
    team_matches = add_rolling_form(team_matches)
    team_matches = add_venue_strength(team_matches)

    home_feats = (
        team_matches.loc[team_matches["is_home"], ["match_id", *HOME_RENAME]]
        .rename(columns=HOME_RENAME)
    )
    away_feats = (
        team_matches.loc[~team_matches["is_home"], ["match_id", *AWAY_RENAME]]
        .rename(columns=AWAY_RENAME)
    )

    features = matches.merge(home_feats, on="match_id", how="left").merge(
        away_feats, on="match_id", how="left"
    )
    features = features.sort_values("date").reset_index(drop=True)

    # League-wide pre-match average goals (expanding window: only earlier
    # matches), used to normalise attack/defence strength below.
    features["league_avg_home_goals"] = features["home_goals"].expanding().mean().shift(1)
    features["league_avg_away_goals"] = features["away_goals"].expanding().mean().shift(1)
    features["league_avg_home_goals"] = features["league_avg_home_goals"].fillna(
        features["home_goals"].mean()
    )
    features["league_avg_away_goals"] = features["league_avg_away_goals"].fillna(
        features["away_goals"].mean()
    )

    # Dixon-Coles style expected-goals proxy:
    #   attack strength   = team's own scoring rate / league average scoring rate
    #   defence weakness  = opponent's own conceding rate / league average conceding rate
    #   proxy xG          = attack strength x defence weakness x league average goals
    home_attack = features["home_venue_goals_for"] / features["league_avg_home_goals"]
    away_defence = features["away_venue_goals_against"] / features["league_avg_home_goals"]
    features["proxy_xg_home"] = home_attack * away_defence * features["league_avg_home_goals"]

    away_attack = features["away_venue_goals_for"] / features["league_avg_away_goals"]
    home_defence = features["home_venue_goals_against"] / features["league_avg_away_goals"]
    features["proxy_xg_away"] = away_attack * home_defence * features["league_avg_away_goals"]

    # Early matches (a team's first ~5 appearances in the dataset) have no
    # rolling history yet -> NaN. Impute with the league-wide median so the
    # table is ready to model without dropping rows.
    prefixes = ("home_form", "away_form", "home_venue", "away_venue", "proxy_xg")
    feature_cols = [c for c in features.columns if c.startswith(prefixes)]
    medians = features[feature_cols].median(numeric_only=True)
    features[feature_cols] = features[feature_cols].fillna(medians)

    return features


def build_feature_table(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    """Load data/processed/matches.csv, engineer features, and write
    data/processed/features.csv."""
    processed_dir = Path(processed_dir)
    matches = pd.read_csv(processed_dir / "matches.csv", parse_dates=["date"])
    features = build_match_features(matches)
    features.to_csv(processed_dir / "features.csv", index=False)
    return features
