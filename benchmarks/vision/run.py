#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import random
import sys
from time import perf_counter

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microfactory.vision.alignment import estimate_alignment  # noqa: E402
from microfactory.vision.verification import VerificationThresholds, decide_verification  # noqa: E402


def render(center, size, angle, image_size=(240, 320)):
    image = np.zeros(image_size, dtype=np.uint8)
    rect = (tuple(center), tuple(size), float(angle))
    box = cv2.boxPoints(rect).astype(np.int32)
    cv2.fillConvexPoly(image, box, 255)
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    thresholds = VerificationThresholds(2, 8, 2, 8, 0.75, 0.25)

    latencies = []
    position_errors = []
    angle_errors = []
    decisions = {"PASS": 0, "RETRY": 0, "FAIL": 0, "HUMAN_REVIEW": 0}
    for _ in range(args.samples):
        expected = (160.0, 120.0)
        dx = rng.uniform(-10, 10)
        dy = rng.uniform(-10, 10)
        angle = rng.uniform(-35, 35)
        image = render((expected[0] + dx, expected[1] + dy), (110, 32), angle)
        started = perf_counter()
        alignment = estimate_alignment(
            image,
            expected_center_px=expected,
            expected_angle_deg=angle,
        )
        decision = decide_verification(alignment, thresholds)
        latencies.append((perf_counter() - started) * 1000.0)
        position_errors.append(abs(alignment.position_error_px - (dx * dx + dy * dy) ** 0.5))
        angle_errors.append(alignment.angle_error_deg)
        decisions[decision.decision.value] += 1

    writer = csv.writer(sys.stdout)
    writer.writerow([
        "samples", "seed", "mean_latency_ms", "p95_latency_ms",
        "mean_position_estimation_error_px", "mean_angle_error_deg",
        "pass", "retry", "fail", "human_review"
    ])
    sorted_latency = sorted(latencies)
    p95_index = max(0, min(len(sorted_latency) - 1, int(0.95 * len(sorted_latency)) - 1))
    writer.writerow([
        args.samples,
        args.seed,
        f"{sum(latencies)/len(latencies):.4f}",
        f"{sorted_latency[p95_index]:.4f}",
        f"{sum(position_errors)/len(position_errors):.4f}",
        f"{sum(angle_errors)/len(angle_errors):.4f}",
        decisions["PASS"], decisions["RETRY"], decisions["FAIL"], decisions["HUMAN_REVIEW"],
    ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
