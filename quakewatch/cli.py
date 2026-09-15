from __future__ import annotations

import argparse
import sys

from quakewatch.fetch import DEFAULT_DAYS, DEFAULT_MIN_MAG, fetch_quakes
from quakewatch.store import connect, list_quakes, upsert_quakes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quakewatch")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch_cmd = sub.add_parser("fetch", help="Fetch USGS events into SQLite")
    fetch_cmd.add_argument("--min-mag", type=float, default=DEFAULT_MIN_MAG)
    fetch_cmd.add_argument("--days", type=int, default=DEFAULT_DAYS)

    list_cmd = sub.add_parser("list", help="List stored events")
    list_cmd.add_argument("--min-mag", type=float, default=DEFAULT_MIN_MAG)
    list_cmd.add_argument("--days", type=int, default=DEFAULT_DAYS)

    return parser


def cmd_fetch(min_mag: float, days: int) -> int:
    quakes = fetch_quakes(days=days, min_mag=min_mag)
    conn = connect()
    try:
        written = upsert_quakes(conn, quakes)
    finally:
        conn.close()
    print(f"fetched {len(quakes)}, wrote {written}")
    return 0


def cmd_list(min_mag: float, days: int) -> int:
    conn = connect()
    try:
        rows = list_quakes(conn, min_mag=min_mag, days=days)
    finally:
        conn.close()
    for row in rows:
        mag = row["mag"]
        mag_text = f"{mag:.1f}" if mag is not None else "?"
        print(f"{row['time_utc']}  M{mag_text}  {row['place']}")
    print(f"{len(rows)} quakes")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "fetch":
        return cmd_fetch(args.min_mag, args.days)
    if args.command == "list":
        return cmd_list(args.min_mag, args.days)
    return 1


if __name__ == "__main__":
    sys.exit(main())
