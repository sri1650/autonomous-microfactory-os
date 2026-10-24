#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from microfactory.fleet.stress import run_stress_case

DEFAULT=[(10,20,range(1,11)),(25,30,range(1,11)),(50,40,range(1,11)),(75,50,range(1,6)),(100,60,range(1,6))]

def percentile(values,p):
    values=sorted(values)
    if not values: return 0.0
    k=(len(values)-1)*p
    lo=int(k); hi=min(lo+1,len(values)-1); f=k-lo
    return values[lo]*(1-f)+values[hi]*f

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path); args=ap.parse_args()
    rows=[]
    for robots,grid,seeds in DEFAULT:
        samples=[run_stress_case(robots,grid_size=grid,seed=s) for s in seeds]
        ms=[s.planner_ms for s in samples]
        rows.append({
            "robots":robots,"grid":grid,"runs":len(samples),
            "p50_ms":percentile(ms,.50),"p95_ms":percentile(ms,.95),
            "max_ms":max(ms),"mean_stretch":statistics.mean(s.path_stretch for s in samples),
            "max_makespan":max(s.makespan for s in samples),
            "all_conflict_free":all(s.conflict_free for s in samples),
        })
    target=args.output.open("w",newline="",encoding="utf-8") if args.output else sys.stdout
    try:
        w=csv.DictWriter(target,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    finally:
        if args.output: target.close()
    return 0 if all(r["all_conflict_free"] for r in rows) else 2
if __name__=="__main__": raise SystemExit(main())
