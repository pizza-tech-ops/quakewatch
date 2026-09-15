from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path("quakes.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS quakes (
    id TEXT PRIMARY KEY,
    time_utc TEXT,
    lat REAL,
    lon REAL,
    mag REAL,
    place TEXT,
    raw_json TEXT
);
"""

UPSERT_SQL = """
INSERT INTO quakes (id, time_utc, lat, lon, mag, place, raw_json)
VALUES (:id, :time_utc, :lat, :lon, :mag, :place, :raw_json)
ON CONFLICT(id) DO UPDATE SET
    time_utc = excluded.time_utc,
    lat = excluded.lat,
    lon = excluded.lon,
    mag = excluded.mag,
    place = excluded.place,
    raw_json = excluded.raw_json;
"""


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(SCHEMA_SQL)
    conn.commit()


def upsert_quakes(
    conn: sqlite3.Connection,
    quakes: list[dict[str, Any]],
) -> int:
    rows = [q for q in quakes if q.get("id")]
    if not rows:
        return 0
    conn.executemany(UPSERT_SQL, rows)
    conn.commit()
    return len(rows)
