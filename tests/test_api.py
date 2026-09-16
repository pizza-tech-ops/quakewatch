from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from quakewatch.api import app
from quakewatch.store import connect, upsert_quakes


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _quake(event_id, mag=2.7, place="Newberg, Oregon", time_utc=None):
    if time_utc is None:
        time_utc = _iso(datetime.now(timezone.utc))
    return {
        "id": event_id,
        "time_utc": time_utc,
        "lat": 45.28,
        "lon": -123.10,
        "mag": mag,
        "place": place,
        "raw_json": '{"id": "%s"}' % event_id,
    }


def _client(tmp_path: Path, monkeypatch):
    db = tmp_path / "quakes.db"
    monkeypatch.setenv("QUAKEWATCH_DB", str(db))
    conn = connect(db)
    conn.close()
    return TestClient(app), db


def test_health_ok(tmp_path, monkeypatch):
    client, _db = _client(tmp_path, monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_quakes_empty(tmp_path, monkeypatch):
    client, _db = _client(tmp_path, monkeypatch)
    response = client.get("/quakes")
    assert response.status_code == 200
    assert response.json() == []


def test_quakes_returns_seeded_row(tmp_path, monkeypatch):
    client, db = _client(tmp_path, monkeypatch)
    conn = connect(db)
    try:
        upsert_quakes(conn, [_quake("uw12345678", mag=2.7)])
    finally:
        conn.close()

    response = client.get("/quakes")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "uw12345678"
    assert body[0]["mag"] == 2.7
    assert body[0]["place"] == "Newberg, Oregon"


def test_quakes_min_mag_query(tmp_path, monkeypatch):
    client, db = _client(tmp_path, monkeypatch)
    now = datetime.now(timezone.utc)
    conn = connect(db)
    try:
        upsert_quakes(
            conn,
            [
                _quake("small", mag=2.1, time_utc=_iso(now)),
                _quake("big", mag=3.4, time_utc=_iso(now)),
            ],
        )
    finally:
        conn.close()

    response = client.get("/quakes", params={"min_mag": 2.5, "days": 30})
    assert response.status_code == 200
    ids = [row["id"] for row in response.json()]
    assert ids == ["big"]


def test_quakes_days_query(tmp_path, monkeypatch):
    client, db = _client(tmp_path, monkeypatch)
    now = datetime.now(timezone.utc)
    conn = connect(db)
    try:
        upsert_quakes(
            conn,
            [
                _quake("fresh", mag=3.0, time_utc=_iso(now - timedelta(days=1))),
                _quake("stale", mag=3.0, time_utc=_iso(now - timedelta(days=20))),
            ],
        )
    finally:
        conn.close()

    response = client.get("/quakes", params={"min_mag": 2.5, "days": 7})
    assert response.status_code == 200
    ids = [row["id"] for row in response.json()]
    assert ids == ["fresh"]
