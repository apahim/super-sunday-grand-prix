#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


CANONICAL_NAMES = {
    "Sean OConnor": "Sean O'Connor",
    "Darragh Flannagan": "Darragh Flanagan",
}


def canonical_name(name):
    return CANONICAL_NAMES.get(name, name)


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


def normalized_results(race):
    seen = set()
    results = []
    for entry in race["results"]:
        name = canonical_name(entry["name"])
        if name in seen:
            continue
        seen.add(name)
        normalized = dict(entry)
        normalized["name"] = name
        results.append(normalized)
    return results


def score_race(race):
    race_points = []
    for i, entry in enumerate(normalized_results(race), start=1):
        points = base_points(i)
        race_points.append((i, entry, points))
    return race_points


def aggregate(races):
    stats = {}
    for race in races:
        for i, entry, points in score_race(race):
            name = entry["name"]
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
        for i, entry, points in score_race(race):
            print(f"  {i:2d}. {entry['name']:<28} {points:2d} pts")
        print()


def print_overall(stats, sort_key):
    print(f"{'Driver':<30}{'Races':>6}{'Total':>8}{'Avg':>8}")
    print("-" * 52)
    for name, s in sorted(stats.items(), key=lambda kv: (-kv[1][sort_key], kv[0])):
        print(f"{name:<30}{s['races']:>6}{s['total']:>8}{s['avg']:>8.2f}")


def standings_rows(stats):
    return sorted(stats.items(), key=lambda kv: (-kv[1]["total"], kv[0]))


def standings_table(stats, limit=None):
    rows = standings_rows(stats)
    if limit is not None:
        rows = rows[:limit]

    lines = [
        "| Rank | Driver | Races | Total | Avg |",
        "|---:|---|---:|---:|---:|",
    ]
    for rank, (name, s) in enumerate(rows, start=1):
        lines.append(
            f"| {rank} | {name} | {s['races']} | {s['total']} | {s['avg']:.2f} |"
        )
    return "\n".join(lines)


def race_table(race):
    lines = [
        "| Position | Driver | Kart | Best Lap | Gap | Points |",
        "|---:|---|---:|---|---:|---:|",
    ]
    for position, entry, points in score_race(race):
        kart = entry["kart"] if entry["kart"] is not None else ""
        gap = entry["gap"] or ""
        lines.append(
            f"| {position} | {entry['name']} | {kart} | {entry['best_lap']} | {gap} | {points} |"
        )
    return "\n".join(lines)


def write_markdown(races, stats):
    race_links = "\n".join(
        f"| [{race.get('race', f'Race {i}')}]({Path('races') / f'race{i}.md'}) |"
        for i, race in enumerate(races, start=1)
    )
    readme = f"""# Super Sunday Grand Prix Standings

Held at Kiltorcan Raceway.

Standings after {len(races)} races, sorted by total points.

## Top 10 Driver Standings

{standings_table(stats, limit=10)}

[Full standings](standings.md)

## Race Results

| Race |
|---|
{race_links}
"""
    Path("README.md").write_text(readme, encoding="utf-8")

    standings = f"""# Full Standings

Standings after {len(races)} races, sorted by total points.

{standings_table(stats)}
"""
    Path("standings.md").write_text(standings, encoding="utf-8")

    for i, race in enumerate(races, start=1):
        path = Path("races") / f"race{i}.md"
        title = race.get("race", f"Race {i}")
        content = f"""# {title} Results

{race_table(race)}
"""
        path.write_text(content, encoding="utf-8")


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
    parser.add_argument(
        "--write-markdown",
        action="store_true",
        help="write README, full standings, and per-race markdown files",
    )
    args = parser.parse_args()

    races = load_races(args.directory)
    if not races:
        print(f"No race JSON files found in {args.directory!r}.", file=sys.stderr)
        sys.exit(1)

    print_race_tables(races)
    stats = aggregate(races)
    print_overall(stats, args.sort)
    if args.write_markdown:
        write_markdown(races, stats)


if __name__ == "__main__":
    main()
