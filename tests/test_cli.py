import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"tools/microfactory.py"

def run(*args):
    return subprocess.run([sys.executable,str(CLI),*args],cwd=ROOT,capture_output=True,text=True)

def test_validate_job():
    r=run("validate-job","scenarios/jobs/pcb_batch_104.yaml")
    assert r.returncode==0
    assert json.loads(r.stdout)["valid"] is True

def test_stress_cli():
    r=run("stress","--robots","10","--grid","20","--seed","1")
    assert r.returncode==0
    assert json.loads(r.stdout)["conflict_free"] is True

def test_fault_cli_is_json():
    r=run("faults","--robots","3","--count","4","--seed","7")
    assert r.returncode==0
    assert len(json.loads(r.stdout))==4
