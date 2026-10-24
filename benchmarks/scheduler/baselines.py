#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, sys
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))

from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.domain.models import JobRecord, TaskDefinition, TaskRecord
from microfactory.orchestrator import Orchestrator
from microfactory.scheduler.heuristics import Heuristic, rank_ready_tasks


@dataclass(frozen=True)
class Result:
    strategy:str
    makespan:float
    mean_lateness:float
    total_tardiness:float
    weighted_tardiness:float


def load_workload(path:Path):
    raw=json.loads(path.read_text())
    jobs=[]
    for item in raw["jobs"]:
        repo=InMemoryJobRepository(); svc=Orchestrator(repo,InMemoryEventSink())
        job=JobRecord(item["id"],int(item["priority"]),{
            "work":TaskRecord(TaskDefinition("work","PROCESS","machine",payload={
                "duration":float(item["duration"]),
                "due_tick":float(item["due_tick"]),
            }))
        })
        jobs.append(svc.submit_job(job,command_id=f"submit:{item['id']}").job)
    return jobs


def evaluate(jobs,strategy:Heuristic):
    order=rank_ready_tasks(jobs,strategy)
    now=0.0; lateness=[]; tardiness=[]; weighted=[]
    for item in order:
        duration=float(item.task.definition.payload["duration"])
        due=float(item.task.definition.payload["due_tick"])
        now+=duration
        late=now-due
        lateness.append(late)
        tard=max(0.0,late)
        tardiness.append(tard)
        weighted.append(tard*max(1,item.job.priority))
    return Result(strategy.value,now,sum(lateness)/len(lateness),sum(tardiness),sum(weighted))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario",type=Path,default=ROOT/"scenarios/scheduler/baseline_workload.json")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    jobs=load_workload(args.scenario)
    rows=[evaluate(jobs,s) for s in Heuristic]
    target=args.output.open("w",newline="",encoding="utf-8") if args.output else sys.stdout
    try:
        w=csv.writer(target)
        w.writerow(["strategy","makespan","mean_lateness","total_tardiness","weighted_tardiness"])
        for r in rows: w.writerow([r.strategy,r.makespan,r.mean_lateness,r.total_tardiness,r.weighted_tardiness])
    finally:
        if args.output: target.close()
    return 0
if __name__=="__main__": raise SystemExit(main())
