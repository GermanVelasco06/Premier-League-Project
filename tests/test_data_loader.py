from pathlib import Path

import pytest

from src.data_loader import (
    load_all_seasons,
    load_season_file,
    season_from_filename,
)

RAW_CSV = (
    "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HTHG,HTAG,HTR,Referee,"
    "HS,AS,HST,AST,HF,AF,HC,AC,HY,AY,HR,AR,B365H,B365D,B365A\n"
    "E0,11/08/2023,20:00,Burnley,Man City,0,3,A,0,2,A,C Pawson,"
    "6,17,1,8,11,8,6,5,0,0,1,0,8,5.5,1.33\n"
    "E0,12/08/2023,12:30,Arsenal,Nott'm Forest,2,1,H,2,0,H,M Oliver,"
    "15,6,7,2,12,12,8,3,2,2,0,0,1.18,7,15\n"
)


def test_season_from_filename():
    assert season_from_filename(Path("data/raw/E0_2023-24.csv")) == "2023-24"


def test_load_season_file(tmp_path):
    csv_path = tmp_path / "E0_2023-24.csv"
    csv_path.write_text(RAW_CSV)

    df = load_season_file(csv_path)

    assert len(df) == 2
    expected_cols = {"home_team", "away_team", "home_goals", "away_goals", "result", "season"}
    assert expected_cols.issubset(df.columns)
    assert df.loc[0, "home_team"] == "Burnley"
    assert df.loc[0, "home_goals"] == 0
    assert df.loc[0, "away_goals"] == 3
    assert df["season"].unique().tolist() == ["2023-24"]


def test_load_season_file_missing_columns(tmp_path):
    csv_path = tmp_path / "E0_2023-24.csv"
    csv_path.write_text("Div,Date,HomeTeam\nE0,11/08/2023,Burnley\n")

    with pytest.raises(ValueError):
        load_season_file(csv_path)


def test_load_all_seasons(tmp_path):
    (tmp_path / "E0_2022-23.csv").write_text(RAW_CSV)
    (tmp_path / "E0_2023-24.csv").write_text(RAW_CSV)

    matches = load_all_seasons(tmp_path)

    assert len(matches) == 4
    assert matches["season"].nunique() == 2
    assert matches["match_id"].tolist() == list(range(1, 5))


def test_load_all_seasons_no_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_all_seasons(tmp_path)
