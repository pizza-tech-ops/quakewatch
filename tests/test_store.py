from pathlib import Path

from quakewatch.store import connect, upsert_quakes


def _quake(event_id: str, mag: float = 2.7, place: str = "Newberg, Oregon"):
    return {
        "id": event_id,
        "time_utc": "2024-09-15T11:33:20Z",
        "lat": 45.28,
        "lon": -123.10,
        "mag": mag,
        "place": place,
        "raw_json": '{"id": "%s"}' % event_id,
    }


def test_connect_creates_quakes_table(tmp_path: Path):
    db = tmp_path / "quakes.db"
    conn = connect(db)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='quakes'"
        ).fetchall()
        assert len(rows) == 1
    finally:
        conn.close()


def test_upsert_inserts_one_quake(tmp_path: Path):
    conn = connect(tmp_path / "quakes.db")
    try:
        written = upsert_quakes(conn, [_quake("uw12345678")])
        assert written == 1

        row = conn.execute(
            "SELECT id, mag, place, lat, lon, time_utc FROM quakes WHERE id = ?",
            ("uw12345678",),
        ).fetchone()
        assert row["id"] == "uw12345678"
        assert row["mag"] == 2.7
        assert row["place"] == "Newberg, Oregon"
        assert row["lat"] == 45.28
        assert row["lon"] == -123.10
        assert row["time_utc"] == "2024-09-15T11:33:20Z"
    finally:
        conn.close()


def test_upsert_updates_existing_id(tmp_path: Path):
    conn = connect(tmp_path / "quakes.db")
    try:
        upsert_quakes(conn, [_quake("uw12345678", mag=2.7, place="old")])
        written = upsert_quakes(
            conn, [_quake("uw12345678", mag=3.4, place="updated place")]
        )
        assert written == 1

        rows = conn.execute("SELECT mag, place FROM quakes").fetchall()
        assert len(rows) == 1
        assert rows[0]["mag"] == 3.4
        assert rows[0]["place"] == "updated place"
    finally:
        conn.close()


def test_upsert_writes_two_different_ids(tmp_path: Path):
    conn = connect(tmp_path / "quakes.db")
    try:
        written = upsert_quakes(
            conn,
            [
                _quake("uw111"),
                _quake("uw222", mag=3.1, place="Klamath Falls, Oregon"),
            ],
        )
        assert written == 2
        count = conn.execute("SELECT COUNT(*) AS n FROM quakes").fetchone()["n"]
        assert count == 2
    finally:
        conn.close()


def test_upsert_empty_list_writes_nothing(tmp_path: Path):
    conn = connect(tmp_path / "quakes.db")
    try:
        assert upsert_quakes(conn, []) == 0
        count = conn.execute("SELECT COUNT(*) AS n FROM quakes").fetchone()["n"]
        assert count == 0
    finally:
        conn.close()


def test_upsert_skips_rows_without_id(tmp_path: Path):
    conn = connect(tmp_path / "quakes.db")
    try:
        written = upsert_quakes(
            conn,
            [
                {"mag": 4.0, "place": "no id"},
                _quake("uw00000001"),
            ],
        )
        assert written == 1
        ids = [row["id"] for row in conn.execute("SELECT id FROM quakes")]
        assert ids == ["uw00000001"]
    finally:
        conn.close()
