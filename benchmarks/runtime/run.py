#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import socket
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import grpc


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microfactory.contracts.generated import factory_pb2, factory_pb2_grpc


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _percentile(samples: list[float], fraction: float) -> float:
    ordered = sorted(samples)
    return ordered[max(0, min(len(ordered) - 1, round(fraction * len(ordered) + 0.499) - 1))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.samples <= 0:
        raise ValueError("samples must be positive")

    port = _free_port()
    process = subprocess.Popen(
        ["cargo", "run", "--quiet", "-p", "robot_runtime", "--bin", "robot_runtime_server", "--", f"127.0.0.1:{port}", "robot-bench"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    try:
        assert process.stdout is not None and process.stdout.readline().startswith("READY ")
        grpc.channel_ready_future(channel).result(timeout=10)
        stub = factory_pb2_grpc.RobotRuntimeStub(channel)
        command = factory_pb2.RobotCommand(
            command_id="benchmark-command",
            correlation_id="benchmark",
            robot_id="robot-bench",
            kind="MOVE",
        )
        first = stub.SubmitCommand(command, timeout=10)
        if first.disposition != factory_pb2.COMMAND_DISPOSITION_ACCEPTED:
            raise RuntimeError("runtime did not accept benchmark command")

        submit_ms = []
        status_ms = []
        request = factory_pb2.RobotStatusRequest(robot_id="robot-bench")
        for _ in range(args.samples):
            started = perf_counter()
            duplicate = stub.SubmitCommand(command, timeout=10)
            submit_ms.append((perf_counter() - started) * 1_000)
            if duplicate != first:
                raise RuntimeError("duplicate response changed")
            started = perf_counter()
            status = stub.GetStatus(request, timeout=10)
            status_ms.append((perf_counter() - started) * 1_000)
            if status.active_command_id != command.command_id:
                raise RuntimeError("status lost active command")

        target = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
        try:
            writer = csv.writer(target)
            writer.writerow(["samples", "submit_p50_ms", "submit_p95_ms", "status_p50_ms", "status_p95_ms"])
            writer.writerow(
                [
                    args.samples,
                    round(_percentile(submit_ms, 0.50), 3),
                    round(_percentile(submit_ms, 0.95), 3),
                    round(_percentile(status_ms, 0.50), 3),
                    round(_percentile(status_ms, 0.95), 3),
                ]
            )
        finally:
            if args.output:
                target.close()
    finally:
        channel.close()
        process.terminate()
        process.wait(timeout=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
