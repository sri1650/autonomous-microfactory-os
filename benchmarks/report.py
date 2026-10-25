#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "docs/generated"
OUT = GENERATED / "performance_report.md"


def read_rows(name: str) -> list[dict[str, str]]:
    path = GENERATED / name
    if not path.exists():
        raise FileNotFoundError(f"required measured artefact is missing: {path}")
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def main() -> int:
    scheduler = read_rows("scheduler_comparison.csv")
    fleet = read_rows("fleet_multiseed_100.csv")
    runtime = read_rows("runtime_grpc.csv")[0]
    vision = read_rows("vision_200.csv")[0]

    lines = [
        "# Final Measured Performance Report",
        "",
        "Measured locally on the development machine. These are software/simulation results, not production SLAs or hardware validation.",
        "",
        "## Scheduler retained workload",
        "",
        "| Strategy | Makespan | Mean lateness | Total tardiness | Weighted tardiness | Compute ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in scheduler:
        lines.append(
            f"| {row['strategy']} | {row['makespan']} | {row['mean_lateness']} | "
            f"{row['total_tardiness']} | {row['weighted_tardiness']} | {row['compute_ms']} |"
        )

    lines += [
        "",
        "CP-SAT and every baseline reached a 39-tick makespan. CP-SAT produced weighted tardiness 227, versus 229 for the best heuristic (EDD).",
        "",
        "## Fleet multi-seed scaling",
        "",
        "| Robots | Grid | Runs | p50 ms | p95 ms | Max ms | Mean stretch | Max makespan | Conflict-free |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for row in fleet:
        lines.append(
            f"| {row['robots']} | {row['grid']} | {row['runs']} | {float(row['p50_ms']):.2f} | "
            f"{float(row['p95_ms']):.2f} | {float(row['max_ms']):.2f} | {float(row['mean_stretch']):.4f} | "
            f"{row['max_makespan']} | {row['all_conflict_free']} |"
        )

    lines += [
        "",
        "## Rust gRPC runtime (loopback, 100 samples)",
        "",
        "| Operation | p50 ms | p95 ms |",
        "|---|---:|---:|",
        f"| Idempotent SubmitCommand | {runtime['submit_p50_ms']} | {runtime['submit_p95_ms']} |",
        f"| GetStatus | {runtime['status_p50_ms']} | {runtime['status_p95_ms']} |",
        "",
        "## Synthetic vision alignment",
        "",
        f"- Samples: **{vision['samples']}**",
        f"- Mean latency: **{vision['mean_latency_ms']} ms**; p95: **{vision['p95_latency_ms']} ms**",
        f"- Mean position error: **{vision['mean_position_estimation_error_px']} px**; mean angle error: **{vision['mean_angle_error_deg']}°**",
        "",
        "## Integration evidence",
        "",
        "- Golden E2E: three jobs compose CP-SAT, conflict-free routing, simulated vision, PostgreSQL, three Rust gRPC processes, ClickHouse, and persisted replay.",
        "- Failure E2E: blocked aisle replans after bounded failure, heartbeat loss rejects a mission, and a failed vision pick succeeds after one explicit retry.",
        "- PostgreSQL restart/idempotency, cross-process W3C tracing, and live ClickHouse correlation queries have dedicated integration tests.",
        "",
        "## Honest scope",
        "",
        "All measurements use local software, synthetic fixtures, or simulation. No physical robot/camera validation, production deployment, safety certification, or production-scale load claim is made.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
