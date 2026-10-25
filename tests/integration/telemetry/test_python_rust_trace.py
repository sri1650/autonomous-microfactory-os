from __future__ import annotations

import socket
import subprocess
from pathlib import Path

import grpc
from opentelemetry.sdk.trace import TracerProvider

from microfactory.contracts.generated import factory_pb2, factory_pb2_grpc
from microfactory.telemetry.tracing import inject_trace_context


ROOT = Path(__file__).resolve().parents[3]


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def test_python_trace_context_reaches_rust_grpc_span():
    port = free_port()
    server = subprocess.Popen(
        [
            "cargo",
            "run",
            "--quiet",
            "-p",
            "robot_runtime",
            "--bin",
            "robot_runtime_server",
            "--",
            f"127.0.0.1:{port}",
            "robot-traced",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert server.stdout is not None
        assert server.stdout.readline().startswith("READY ")
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        grpc.channel_ready_future(channel).result(timeout=10)
        stub = factory_pb2_grpc.RobotRuntimeStub(channel)

        provider = TracerProvider()
        tracer = provider.get_tracer("python-rust-trace-test")
        with tracer.start_as_current_span("python.submit") as parent:
            carrier = inject_trace_context()
            _, call = stub.SubmitCommand.with_call(
                factory_pb2.RobotCommand(
                    command_id="cmd-traced",
                    correlation_id="job-traced",
                    robot_id="robot-traced",
                    kind="MOVE",
                ),
                metadata=tuple(carrier.items()),
                timeout=10,
            )
            metadata = dict(call.initial_metadata())
            assert metadata["x-microfactory-parent-trace-id"] == (
                f"{parent.get_span_context().trace_id:032x}"
            )
            assert metadata["x-microfactory-trace-id"] == (
                f"{parent.get_span_context().trace_id:032x}"
            )
            assert len(metadata["x-microfactory-span-id"]) == 16
            assert metadata["x-microfactory-span-id"] != (
                f"{parent.get_span_context().span_id:016x}"
            )
        channel.close()
    finally:
        server.terminate()
        server.wait(timeout=10)
