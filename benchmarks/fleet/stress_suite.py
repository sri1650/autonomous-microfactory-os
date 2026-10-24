#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microfactory.fleet.stress import run_stress_suite  # noqa: E402

DEFAULT_CASES = [
    (10, 20, 1),
    (25, 30, 2),
    (50, 40, 3),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = run_stress_suite(DEFAULT_CASES)
    target = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.writer(target)
        writer.writerow(["robots","seed","grid_size","planner_ms","total_steps","direct_steps","path_stretch","makespan","conflict_free"])
        for r in rows:
            writer.writerow([r.robots,r.seed,r.grid_size,f"{r.planner_ms:.3f}",r.total_steps,r.direct_steps,f"{r.path_stretch:.4f}",r.makespan,int(r.conflict_free)])
    finally:
        if args.output:
            target.close()
    return 0 if all(r.conflict_free for r in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
