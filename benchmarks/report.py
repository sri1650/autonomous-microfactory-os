#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/generated/performance_report.md"


def read_one(path: Path):
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else None


def main() -> int:
    fleet5 = read_one(ROOT / "docs/generated/fleet_05.csv")
    fleet20 = read_one(ROOT / "docs/generated/fleet_20.csv")
    vision = read_one(ROOT / "docs/generated/vision_200.csv")
    cbs_path = ROOT / "docs/generated/fleet_cbs_comparison.csv"
    cbs_rows = []
    if cbs_path.exists():
        with cbs_path.open(newline="", encoding="utf-8") as f:
            cbs_rows = list(csv.DictReader(f))

    lines = [
        "# Pre-integration Performance Evidence",
        "",
        "Generated from measured local benchmark artefacts. These figures are environment-specific and are not production SLAs.",
        "",
        "## Fleet routing",
        "",
        "| Robots | Planner ms | Total steps | Path stretch | Completion tick | Vertex conflicts | Edge swaps |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in (fleet5, fleet20):
        if row:
            lines.append(
                f"| {row['robots']} | {row['planner_ms']} | {row['total_steps']} | {row['path_stretch']} | "
                f"{row['completion_tick']} | {row['vertex_conflicts']} | {row['edge_swaps']} |"
            )
    lines += ["", "## CBS evaluation", "", "| Scenario | Planner | Median ms | p95 ms | Cost | Makespan | Conflict-free |", "|---|---|---:|---:|---:|---:|---|"]
    for row in cbs_rows:
        lines.append(
            f"| {row['scenario']} | {row['planner']} | {float(row['median_ms']):.3f} | "
            f"{float(row['p95_ms']):.3f} | {row['sum_of_costs']} | {row['makespan']} | {row['conflict_free']} |"
        )

    lines += ["", "## Vision alignment", ""]
    if vision:
        lines += [
            f"- Samples: **{vision['samples']}**",
            f"- Mean latency: **{vision['mean_latency_ms']} ms**",
            f"- p95 latency: **{vision['p95_latency_ms']} ms**",
            f"- Mean position-estimation error: **{vision['mean_position_estimation_error_px']} px**",
            f"- Mean angle error: **{vision['mean_angle_error_deg']} deg**",
            f"- Decisions: PASS {vision['pass']}, RETRY {vision['retry']}, FAIL {vision['fail']}, HUMAN_REVIEW {vision['human_review']}",
        ]

    lines += [
        "",
        "## Integration evidence",
        "",
        "- Python vertical slice: three jobs through FIFO scheduling, conflict-free mover routing, vision verification and terminal success.",
        "- Recovery slice: terminal vision-task failure can be explicitly retried, reopens the job, and can then succeed.",
        "- Deterministic simulation replay core validates event ordering, machine transitions and event digest integrity.",
        "- OpenTelemetry Python boundary propagates request span identity into correlated orchestrator events.",
        "",
        "## Pending before final performance report",
        "",
        "- Rust runtime/gRPC command latency and heartbeat detection",
        "- FIFO vs OR-Tools CP-SAT makespan/lateness comparison",
        "- live PostgreSQL restart/idempotency integration",
        "- live ClickHouse ingestion/query measurements",
        "- full Rust + scheduler + database + telemetry E2E scenario",
        "",
        "The final recruiter README must only promote quantitative figures after the corresponding final integration benchmark is retained beside the claim.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
