from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import FastAPI

from quakewatch.fetch import DEFAULT_DAYS, DEFAULT_MIN_MAG
from quakewatch.store import connect, list_quakes

app = FastAPI()


def db_path() -> str:
    return os.environ.get("QUAKEWATCH_DB", "quakes.db")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/quakes")
def get_quakes(
    min_mag: float = DEFAULT_MIN_MAG,
    days: int = DEFAULT_DAYS,
) -> List[Dict[str, Any]]:
    conn = connect(db_path())
    try:
        return list_quakes(conn, min_mag=min_mag, days=days)
    finally:
        conn.close()
