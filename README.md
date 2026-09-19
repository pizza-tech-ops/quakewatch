
```markdown
# QuakeWatch

[![test](https://github.com/pizza-tech-ops/quakewatch/actions/workflows/test.yml/badge.svg)](https://github.com/pizza-tech-ops/quakewatch/actions/workflows/test.yml)

Oregon-box earthquake tool. Pulls USGS FDSN events into SQLite, lists them from a CLI, and serves the same rows from a thin FastAPI.

fetch → store → list → API → Docker → CI.

## What it does

- Fetches GeoJSON from the USGS FDSN event API for a fixed Oregon bounding box
- Upserts events into SQLite on USGS event `id`
- Lists stored events from the CLI (`min_mag` + lookback `days`, newest first)
- Serves `GET /health` and `GET /quakes` from the same `list_quakes` store
- Runs in Docker Compose
- Runs pytest on every push to `main` via GitHub Actions

The API **does not** call USGS. `GET /quakes` only reads the database.

## Defaults

| Knob | Value |
| --- | --- |
| Box | lat `42.0`–`46.3`, lon `-124.6`–`-116.5` |
| Window | last 30 days |
| Min magnitude | `2.5` |
| DB file (CLI) | `./quakes.db` |
| DB file (API / Compose) | `$QUAKEWATCH_DB`, else `quakes.db` |

The box is a rectangle, not the Oregon state line. Events just over the border (for example Castle Rock, WA) can appear.

Schema:

```text
quakes(
  id TEXT PRIMARY KEY,
  time_utc TEXT,
  lat REAL,
  lon REAL,
  mag REAL,
  place TEXT,
  raw_json TEXT
)
```

## Requirements

- Python 3.8+ on the laptop (developed on 3.8.10)
- Docker + Compose for the container path (image is Python 3.12)
- Network only for `fetch` (USGS) and for building/pulling the image

Pinned in `requirements.txt`:

```text
httpx==0.28.1
fastapi==0.124.4
uvicorn==0.33.0
pytest==8.3.4
```

Do not unpin these on a 3.8 laptop. Newer FastAPI drops 3.8.

## Setup

```bash
git clone https://github.com/pizza-tech-ops/quakewatch.git
cd quakewatch
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
```

`quakes.db` and `data/` stay local. They are gitignored.

## CLI

From the repo root, with `PYTHONPATH=.`:

```bash
python -m quakewatch fetch
python -m quakewatch list
python -m quakewatch list --min-mag 3 --days 7
```

`fetch` prints `fetched N, wrote N`.
`list` prints one line per event:

```text
2024-09-15T11:33:20Z  M2.7  10 km WSW of Newberg, Oregon
1 quakes
```

Flags on both commands:

- `--min-mag` (default `2.5`)
- `--days` (default `30`)

The CLI always uses `./quakes.db` in the working directory. It does not read `QUAKEWATCH_DB`.

## API

The API reads whatever path is in `QUAKEWATCH_DB`, or `quakes.db` if that env is unset.

```bash
export PYTHONPATH=.
uvicorn quakewatch.api:app --reload --host 127.0.0.1 --port 8000
```

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}

curl "http://127.0.0.1:8000/quakes?min_mag=3&days=7"
# [] when the DB has no matching rows
```

Each quake object has `id`, `time_utc`, `lat`, `lon`, `mag`, `place`, `raw_json`.

Interactive docs: http://127.0.0.1:8000/docs

Populate the DB with the CLI **before** you expect `/quakes` to return events.

## Docker

```bash
mkdir -p data
docker compose up --build
```

- App listens on `http://127.0.0.1:8000`
- Compose sets `QUAKEWATCH_DB=/data/quakes.db`
- `./data` on the host is bind-mounted to `/data` in the container

An empty `data/quakes.db` is normal. `/health` still returns `{"status":"ok"}`. `/quakes` returns `[]` until that file has rows.

To serve events you already fetched on the host:

```bash
mkdir -p data
cp quakes.db data/quakes.db
docker compose up --build
```

Tests inside the image (optional):

```bash
docker compose run --rm app pytest -q
```

## Tests

18 tests. Fetch is mocked with `tests/fixtures/usgs_sample.geojson`. Store and API tests use a temp SQLite file. Nothing in pytest hits USGS.

```bash
export PYTHONPATH=.
pytest -q
```

CI runs the same command on Python 3.12: .github/workflows/test.yml

## Layout

```text
quakewatch/
  fetch.py      USGS query + GeoJSON parse
  store.py      SQLite connect / schema / upsert / list
  cli.py        argparse fetch + list
  api.py        FastAPI /health + /quakes
  __main__.py
tests/
Dockerfile
docker-compose.yml
requirements.txt
```

## License

MIT.
