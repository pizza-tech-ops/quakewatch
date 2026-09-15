import json
from datetime import datetime, timezone
from pathlib import Path

from quakewatch.fetch import build_query_params, parse_feature_collection

FIXTURE = Path(__file__).parent / "fixtures" / "usgs_sample.geojson"


def test_parse_fixture_extracts_oregon_events():
    payload = json.loads(FIXTURE.read_text())
    quakes = parse_feature_collection(payload)

    assert len(quakes) == 2
    assert quakes[0]["id"] == "uw12345678"
    assert quakes[0]["mag"] == 2.7
    assert quakes[0]["place"] == "10 km WSW of Newberg, Oregon"
    assert quakes[0]["lon"] == -123.10
    assert quakes[0]["lat"] == 45.28
    assert quakes[0]["time_utc"] == "2024-09-15T11:33:20Z"
    assert "uw12345678" in quakes[0]["raw_json"]


def test_parse_skips_features_without_id():
    payload = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"mag": 4.0}},
            {
                "type": "Feature",
                "id": "uw00000001",
                "properties": {"mag": 2.5, "place": "test", "time": 0},
                "geometry": {"type": "Point", "coordinates": [-122.0, 44.0, 1.0]},
            },
        ],
    }
    quakes = parse_feature_collection(payload)
    assert [q["id"] for q in quakes] == ["uw00000001"]


def test_build_query_params_uses_oregon_box():
    now = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    params = build_query_params(days=30, min_mag=2.5, now=now)

    assert params["format"] == "geojson"
    assert params["minlatitude"] == "42.0"
    assert params["maxlatitude"] == "46.3"
    assert params["minlongitude"] == "-124.6"
    assert params["maxlongitude"] == "-116.5"
    assert params["minmagnitude"] == "2.5"
    assert params["starttime"] == "2026-08-16T00:00:00"
    assert params["endtime"] == "2026-09-15T00:00:00"
