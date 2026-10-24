#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from microfactory.dsl import load_job_spec
from microfactory.fleet.stress import run_stress_case
from microfactory.chaos import generate_fault_schedule


def main():
    p=argparse.ArgumentParser(prog="microfactory")
    sub=p.add_subparsers(dest="cmd",required=True)

    v=sub.add_parser("validate-job")
    v.add_argument("path",type=Path)

    s=sub.add_parser("stress")
    s.add_argument("--robots",type=int,required=True)
    s.add_argument("--grid",type=int,required=True)
    s.add_argument("--seed",type=int,default=1)

    f=sub.add_parser("faults")
    f.add_argument("--robots",type=int,default=5)
    f.add_argument("--count",type=int,default=8)
    f.add_argument("--horizon",type=int,default=100)
    f.add_argument("--seed",type=int,default=1)

    args=p.parse_args()
    if args.cmd=="validate-job":
        job=load_job_spec(args.path)
        print(json.dumps({"valid":True,"job_id":job.job_id,"tasks":len(job.tasks)},sort_keys=True))
        return 0
    if args.cmd=="stress":
        r=run_stress_case(args.robots,grid_size=args.grid,seed=args.seed)
        print(json.dumps({
            "robots":r.robots,"planner_ms":round(r.planner_ms,3),
            "path_stretch":round(r.path_stretch,4),"makespan":r.makespan,
            "conflict_free":r.conflict_free
        },sort_keys=True))
        return 0 if r.conflict_free else 2
    if args.cmd=="faults":
        ids=[f"r{i:03d}" for i in range(args.robots)]
        rows=generate_fault_schedule(ids,seed=args.seed,horizon=args.horizon,count=args.count)
        print(json.dumps([{
            "tick":x.tick,"resource_id":x.resource_id,"fault_type":x.fault_type.value,"magnitude":x.magnitude
        } for x in rows],sort_keys=True))
        return 0
    return 2
if __name__=="__main__": raise SystemExit(main())
