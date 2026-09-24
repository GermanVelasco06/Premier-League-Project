from scripts.download_clubs import clean_clubs

SAMPLE_PAYLOAD = {
    "response": [
        {
            "team": {
                "id": 42,
                "name": "Arsenal",
                "code": "ARS",
                "country": "England",
                "founded": 1886,
                "logo": "https://media.api-sports.io/football/teams/42.png",
            },
            "venue": {
                "name": "Emirates Stadium",
                "city": "London",
                "capacity": 60704,
            },
        },
        {
            "team": {
                "id": 50,
                "name": "Manchester City",
                "code": "MCI",
                "country": "England",
                "founded": 1880,
                "logo": "https://media.api-sports.io/football/teams/50.png",
            },
            "venue": {
                "name": "Etihad Stadium",
                "city": "Manchester",
                "capacity": 55097,
            },
        },
    ]
}


def test_clean_clubs_flattens_expected_fields():
    records = clean_clubs(SAMPLE_PAYLOAD)

    assert len(records) == 2
    assert records[0]["name"] == "Arsenal"
    assert records[0]["team_id"] == 42
    assert records[0]["venue_name"] == "Emirates Stadium"
    assert records[0]["venue_capacity"] == 60704


def test_clean_clubs_handles_empty_response():
    assert clean_clubs({"response": []}) == []
    assert clean_clubs({}) == []


def test_clean_clubs_handles_missing_venue():
    payload = {"response": [{"team": {"id": 1, "name": "Test FC"}}]}
    records = clean_clubs(payload)
    assert records[0]["venue_name"] is None
