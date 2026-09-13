#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def base_points(position):
    if position == 1:
        return 25
    if position == 2:
        return 20
    if position == 3:
        return 18
    if position == 4:
        return 16
    if 5 <= position <= 19:
        return 20 - position
    return 0


def load_races(directory):
    races = []
    for path in sorted(Path(directory).glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        races.append(data)
    return races


def score_race(race):
    race_points = []
    for i, entry in enumerate(race["results"], start=1):
        points = base_points(i)
        race_points.append((i, entry["name"], points))
    return race_points


def aggregate(races):
    stats = {}
    for race in races:
        for i, name, points in score_race(race):
            s = stats.setdefault(name, {"races": 0, "total": 0, "positions": []})
            s["races"] += 1
            s["total"] += points
            s["positions"].append(i)
    for s in stats.values():
        s["avg"] = s["total"] / s["races"]
    return stats


def print_race_tables(races):
    for race in races:
        print(f"{race.get('race', 'Race')}")
        for i, name, points in score_race(race):
            print(f"  {i:2d}. {name:<28} {points:2d} pts")
        print()


def print_overall(stats, sort_key):
    print(f"{'Driver':<30}{'Races':>6}{'Total':>8}{'Avg':>8}")
    print("-" * 52)
    for name, s in sorted(stats.items(), key=lambda kv: (-kv[1][sort_key], kv[0])):
        print(f"{name:<30}{s['races']:>6}{s['total']:>8}{s['avg']:>8.2f}")


def main():
    parser = argparse.ArgumentParser(description="Score kart race results by position.")
    parser.add_argument(
        "directory",
        nargs="?",
        default="races",
        help="directory containing one JSON file per race (default: races)",
    )
    parser.add_argument(
        "--sort",
        choices=["total", "avg"],
        default="total",
        help="sort the standings by total or average points (default: total)",
    )
    args = parser.parse_args()

    races = load_races(args.directory)
    if not races:
        print(f"No race JSON files found in {args.directory!r}.", file=sys.stderr)
        sys.exit(1)

    print_race_tables(races)
    stats = aggregate(races)
    print_overall(stats, args.sort)


if __name__ == "__main__":
    main()
