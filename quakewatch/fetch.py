from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

MIN_LAT = 42.0
MAX_LAT = 46.3
MIN_LON = -124.6
MAX_LON = -116.5
DEFAULT_DAYS = 30
DEFAULT_MIN_MAG = 2.5


def build_query_params(
    *,
    days: int = DEFAULT_DAYS,
    min_mag: float = DEFAULT_MIN_MAG,
    now: datetime | None = None,
) -> dict[str, str]:
    if now is None:
        now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    return {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "minlatitude": str(MIN_LAT),
        "maxlatitude": str(MAX_LAT),
        "minlongitude": str(MIN_LON),
        "maxlongitude": str(MAX_LON),
        "minmagnitude": str(min_mag),
        "orderby": "time",
    }


def _ms_to_utc(ms: int | float | None) -> str | None:
    if ms is None:
        return None
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    event_id = feature.get("id")
    if not event_id:
        return None

    props = feature.get("properties") or {}
    geom = feature.get("geometry") or {}
    coords = geom.get("coordinates") or []

    lon = coords[0] if len(coords) > 0 else None
    lat = coords[1] if len(coords) > 1 else None

    return {
        "id": event_id,
        "time_utc": _ms_to_utc(props.get("time")),
        "lat": lat,
        "lon": lon,
        "mag": props.get("mag"),
        "place": props.get("place"),
        "raw_json": json.dumps(feature),
    }


def parse_feature_collection(payload: dict[str, Any]) -> list[dict[str, Any]]:
    features = payload.get("features") or []
    quakes: list[dict[str, Any]] = []
    for feature in features:
        parsed = parse_feature(feature)
        if parsed is not None:
            quakes.append(parsed)
    return quakes


def fetch_quakes(
    *,
    days: int = DEFAULT_DAYS,
    min_mag: float = DEFAULT_MIN_MAG,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    params = build_query_params(days=days, min_mag=min_mag)
    owns_client = client is None
    if client is None:
        client = httpx.Client(timeout=30.0)
    try:
        response = client.get(USGS_URL, params=params)
        response.raise_for_status()
        return parse_feature_collection(response.json())
    finally:
        if owns_client:
            client.close()
