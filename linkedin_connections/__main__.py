"""Command-line interface for the LinkedIn connections toolkit.

Run against your own export:

    python -m linkedin_connections summary Connections.csv
    python -m linkedin_connections companies Connections.csv --limit 30
    python -m linkedin_connections summary Connections.csv --json > report.json

Every subcommand takes the path to a ``Connections.csv`` export. Use ``--json``
for machine-readable output; the default is a readable text report.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import analyze
from .parse import load_connections


def _print_summary(data: dict) -> None:
    print(f"Total connections: {data['total']}")
    ref = data["as_of_year"]

    print("\nConnections by year:")
    for year, count in data["by_year"].items():
        bar = "#" * min(count, 50)
        print(f"  {year}  {count:>5}  {bar}")

    print("\nSeniority (title-keyword estimate):")
    for level, count in data["seniority"].items():
        print(f"  {level:<12} {count:>5}")

    print(f"\nTop companies:")
    for company, count in data["top_companies"]:
        print(f"  {count:>5}  {company}")

    st = data["staleness"]
    print(
        f"\nStaleness (stale = connected more than "
        f"{data['stale_after_years']} years before {ref}):"
    )
    print(f"  active   {st['active']:>5}")
    print(f"  stale    {st['stale']:>5}")
    print(f"  undated  {st['undated']:>5}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="linkedin-connections",
        description="Parse and analyze a LinkedIn Connections.csv export.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    # Shared options every subcommand accepts (so `<cmd> file --json` works).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("csv", help="Path to Connections.csv")
    common.add_argument("--json", action="store_true", help="Emit JSON instead of text")

    p_sum = sub.add_parser("summary", parents=[common], help="Run all analyses")
    p_sum.add_argument("--limit", type=int, default=20, help="Top-companies limit")
    p_sum.add_argument(
        "--stale-after-years", type=int, default=4,
        help="Age in years past which a connection counts as stale (default 4)",
    )
    p_sum.add_argument(
        "--as-of-year", type=int, default=None,
        help="Reference year for staleness (default: latest year in the data)",
    )

    sub.add_parser("years", parents=[common], help="Connections per year")

    p_co = sub.add_parser("companies", parents=[common], help="Most common companies")
    p_co.add_argument("--limit", type=int, default=20, help="How many to show")

    sub.add_parser("seniority", parents=[common], help="Seniority breakdown by title keywords")

    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        connections = load_connections(args.csv)
    except FileNotFoundError:
        print(f"File not found: {args.csv}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.command == "summary":
        result: object = analyze.summary(
            connections,
            company_limit=args.limit,
            stale_after_years=args.stale_after_years,
            as_of_year=args.as_of_year,
        )
    elif args.command == "years":
        result = analyze.by_year(connections)
    elif args.command == "companies":
        result = analyze.top_companies(connections, args.limit)
    elif args.command == "seniority":
        result = analyze.seniority(connections)
    else:  # unreachable: subparsers are required
        return 2

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "summary":
        _print_summary(result)  # type: ignore[arg-type]
    elif args.command == "companies":
        for company, count in result:  # type: ignore[misc]
            print(f"  {count:>5}  {company}")
    else:
        for key, count in result.items():  # type: ignore[union-attr]
            print(f"  {key}  {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
