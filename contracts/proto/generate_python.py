from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROTO_DIR = ROOT / "contracts" / "proto"
OUTPUT_DIR = ROOT / "src" / "microfactory" / "contracts" / "generated"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "__init__.py").touch()
    returncode = subprocess.call(
        [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{PROTO_DIR}",
            f"--python_out={OUTPUT_DIR}",
            f"--grpc_python_out={OUTPUT_DIR}",
            str(PROTO_DIR / "factory.proto"),
        ],
        cwd=ROOT,
    )
    if returncode != 0:
        return returncode
    grpc_module = OUTPUT_DIR / "factory_pb2_grpc.py"
    grpc_module.write_text(
        grpc_module.read_text(encoding="utf-8").replace(
            "import factory_pb2 as factory__pb2",
            "from . import factory_pb2 as factory__pb2",
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
