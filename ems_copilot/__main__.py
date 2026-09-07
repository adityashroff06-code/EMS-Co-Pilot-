"""Command-line interface: python -m ems_copilot --help."""

import argparse
import json
from pathlib import Path

from .analytics import EnergyDataset, render_markdown


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only energy analytics and carbon reports.")
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="Validate a database and inspect its time coverage.")
    report = commands.add_parser("report", help="Generate a local JSON or Markdown report.")
    for command in (audit, report):
        command.add_argument("--db", default="ems.db", help="SQLite database (default: ems.db).")
    report.add_argument("--start", required=True, help="Inclusive YYYY-MM-DD.")
    report.add_argument("--end", required=True, help="Inclusive YYYY-MM-DD.")
    report.add_argument("--top-n", type=int, default=5)
    report.add_argument("--format", choices=("markdown", "json"), default="markdown")
    report.add_argument("--output", type=Path, help="Create a new file; existing files are never overwritten.")
    args = parser.parse_args(argv)
    try:
        dataset = EnergyDataset(args.db)
        if args.command == "audit":
            print(json.dumps(dataset.audit(), indent=2))
            return 0
        snapshot = dataset.snapshot(args.start, args.end, args.top_n)
        result = json.dumps(snapshot, indent=2, allow_nan=False) + "\n" if args.format == "json" else render_markdown(snapshot)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as output:
                output.write(result)
            print(f"Report saved: {args.output}")
        else:
            print(result, end="")
        return 0
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
