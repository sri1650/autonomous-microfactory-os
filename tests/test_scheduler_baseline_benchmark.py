import csv, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"benchmarks/scheduler/baselines.py"

def test_baseline_strategies_are_measurable():
    r=subprocess.run([sys.executable,str(SCRIPT)],cwd=ROOT,capture_output=True,text=True)
    assert r.returncode==0
    rows=list(csv.DictReader(r.stdout.splitlines()))
    assert len(rows)==4
    by={x["strategy"]:x for x in rows}
    assert float(by["spt"]["mean_lateness"]) <= float(by["priority"]["mean_lateness"])
    assert all(float(x["makespan"])>0 for x in rows)
