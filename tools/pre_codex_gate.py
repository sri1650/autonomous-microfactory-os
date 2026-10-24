#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(name, cmd, timeout=180):
    started=time.perf_counter()
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    return {
        "name":name,
        "returncode":p.returncode,
        "elapsed_s":round(time.perf_counter()-started,3),
        "stdout_tail":p.stdout[-2000:],
        "stderr_tail":p.stderr[-1000:],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--full",action="store_true",help="also run multi-seed fleet scaling through 100 robots")
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()

    checks=[
        run("pytest",[sys.executable,"-m","pytest","-q"],timeout=120),
        run("compileall",[sys.executable,"-m","compileall","-q","src","tests","apps"],timeout=60),
        run("job_dsl",[sys.executable,"tools/microfactory.py","validate-job","scenarios/jobs/pcb_batch_104.yaml"],timeout=30),
        run("scheduler_baselines",[sys.executable,"benchmarks/scheduler/baselines.py"],timeout=30),
        run("fleet_50",[sys.executable,"tools/microfactory.py","stress","--robots","50","--grid","40","--seed","3"],timeout=60),
    ]
    if args.full:
        checks.append(run("fleet_multiseed_100",[sys.executable,"benchmarks/fleet/multi_seed.py"],timeout=240))

    payload={
        "status":"pass" if all(c["returncode"]==0 for c in checks) else "fail",
        "checks":checks,
        "reserved_for_codex":[
            "Rust runtime + gRPC",
            "OR-Tools CP-SAT",
            "live PostgreSQL adapter/integration",
            "live ClickHouse integration",
            "cross-process trace propagation",
            "persisted full-stack replay",
            "final E2E and recruiter evidence",
        ],
    }
    text=json.dumps(payload,indent=2)
    if args.json_out:
        args.json_out.write_text(text+"\n",encoding="utf-8")
    print(text)
    return 0 if payload["status"]=="pass" else 2

if __name__=="__main__":
    raise SystemExit(main())
