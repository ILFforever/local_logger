"""
query_logs.py — readable stats dump for AI querying.
Usage:
    python query_logs.py              # summary of all runs
    python query_logs.py --run NAME   # detailed stats for one run
    python query_logs.py --latest     # most recent run only
"""

import json
import argparse
from pathlib import Path


LOG_DIR = Path("logs")


def load_runs():
    if not LOG_DIR.exists():
        return []
    runs = []
    for run_dir in sorted(LOG_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        metrics_file = run_dir / "metrics.jsonl"
        if not metrics_file.exists():
            continue
        run = {"name": run_dir.name, "path": run_dir, "config": {}, "summary": {}, "metrics": []}
        config_file = run_dir / "config.json"
        if config_file.exists():
            run["config"] = json.loads(config_file.read_text())
        summary_file = run_dir / "summary.json"
        if summary_file.exists():
            run["summary"] = json.loads(summary_file.read_text())
        for line in metrics_file.read_text().splitlines():
            if line.strip():
                run["metrics"].append(json.loads(line))
        runs.append(run)
    return runs


def fmt(val, decimals=6):
    return f"{val:.{decimals}f}" if isinstance(val, float) else str(val)


def print_run_summary(run, detailed=False):
    cfg = run["config"]
    summary = run["summary"]
    metrics = run["metrics"]

    print(f"\n{'='*60}")
    print(f"RUN: {run['name']}")
    print(f"  Project : {cfg.get('project', 'N/A')}")
    print(f"  Started : {cfg.get('start_time', 'N/A')}")
    print(f"  Ended   : {summary.get('end_time', 'still running' if not summary else 'N/A')}")
    print(f"  Steps   : {summary.get('total_steps', len(metrics))}")

    ms = summary.get("metrics_summary", {})
    if ms:
        print("\n  METRIC SUMMARY:")
        for metric, stats in ms.items():
            print(f"    {metric}:")
            print(f"      final={fmt(stats['final'])}  min={fmt(stats['min'])}  max={fmt(stats['max'])}  mean={fmt(stats['mean'])}")

    if detailed and metrics:
        print("\n  ALL EPOCHS:")
        header_keys = [k for k in metrics[0] if k != "timestamp"]
        header = "  ".join(f"{k:>14}" for k in header_keys)
        print(f"  {header}")
        print(f"  {'-' * len(header)}")
        for entry in metrics:
            row = "  ".join(f"{fmt(entry.get(k, ''), 6):>14}" for k in header_keys)
            print(f"  {row}")

    if metrics:
        latest = metrics[-1]
        print("\n  LATEST VALUES:")
        for k, v in latest.items():
            if k not in ("step", "timestamp"):
                print(f"    {k}: {fmt(v)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=str, help="Run name to inspect")
    parser.add_argument("--latest", action="store_true", help="Show only the most recent run")
    parser.add_argument("--all", action="store_true", help="Show all epochs for each run")
    args = parser.parse_args()

    runs = load_runs()
    if not runs:
        print("No runs found in logs/")
        return

    if args.run:
        match = [r for r in runs if args.run in r["name"]]
        if not match:
            print(f"No run matching '{args.run}' found.")
            print("Available runs:")
            for r in runs:
                print(f"  {r['name']}")
            return
        for r in match:
            print_run_summary(r, detailed=True)
    elif args.latest:
        print_run_summary(runs[0], detailed=args.all)
    else:
        print(f"Found {len(runs)} run(s):")
        for r in runs:
            print_run_summary(r, detailed=args.all)


if __name__ == "__main__":
    main()
