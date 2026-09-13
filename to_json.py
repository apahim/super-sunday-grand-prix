#!/usr/bin/env python3
import argparse
import json
import re
import sys

_NUMBER = re.compile(r"^#(\d+)\s+(.+)$")


def convert(table_lines):
    header = table_lines[0]
    if "Name" not in header or "Best Lap" not in header:
        print("Expected header row: POS  Name  Best Lap  Gap", file=sys.stderr)
        sys.exit(1)

    results = []
    for line in table_lines[1:]:
        fields = [f.strip() for f in line.split("\t")]
        fields = [f for f in fields if f]
        if not fields:
            continue
        name = fields[1] if len(fields) > 1 else fields[0]
        best_lap = fields[2] if len(fields) > 2 else ""
        gap = fields[3] if len(fields) > 3 else ""

        match = _NUMBER.match(name)
        if match:
            kart = int(match.group(1))
            name = match.group(2).strip()
        else:
            kart = None

        results.append(
            {"name": name, "kart": kart, "best_lap": best_lap, "gap": gap}
        )
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Convert a pasted race table (POS/Name/Best Lap/Gap) into a race JSON file."
    )
    parser.add_argument("outfile", help="output JSON file path")
    parser.add_argument("--race", default="", help="race label (defaults to filename)")
    args = parser.parse_args()

    table = sys.stdin.read().splitlines()
    results = convert(table)

    race_label = args.race or "Race 1"
    data = {"race": race_label, "results": results}
    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {len(results)} results to {args.outfile}")
    print("Then run: python points.py")


if __name__ == "__main__":
    main()