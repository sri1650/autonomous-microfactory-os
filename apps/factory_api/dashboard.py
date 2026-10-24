from __future__ import annotations
import json


def demo_snapshot():
    return {
        "mode":"simulation-preview",
        "jobs":[
            {"id":"PCB-104","state":"RUNNING","stage":"placement"},
            {"id":"PCB-105","state":"INSPECTION","stage":"vision"},
            {"id":"PCB-106","state":"SUCCEEDED","stage":"storage"},
        ],
        "robots":[
            {"id":"mover-01","state":"MOVING","x":5,"y":3,"battery":82},
            {"id":"mover-02","state":"WAITING","x":9,"y":6,"battery":61},
            {"id":"mover-03","state":"DOCKED","x":14,"y":2,"battery":94},
        ],
        "stations":[
            {"id":"printer-1","state":"BUSY","x":3,"y":2},
            {"id":"vision-1","state":"READY","x":8,"y":2},
            {"id":"gantry-1","state":"BUSY","x":12,"y":5},
        ],
        "events":[
            {"tick":81,"text":"PCB-104 assigned to mover-01"},
            {"tick":82,"text":"mover-01 route accepted"},
            {"tick":83,"text":"vision-1 verification PASS"},
        ],
    }


def dashboard_html() -> str:
    payload=json.dumps(demo_snapshot())
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Autonomous Microfactory OS</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#0c1117;color:#d8e2ea;margin:0}}
header{{padding:18px 24px;border-bottom:1px solid #26313b;display:flex;justify-content:space-between}}
.badge{{padding:4px 8px;border:1px solid #58636e;border-radius:999px;font-size:12px}}
main{{display:grid;grid-template-columns:1.3fr 1fr;gap:16px;padding:16px}}
.card{{background:#111923;border:1px solid #26313b;border-radius:10px;padding:14px}}
table{{width:100%;border-collapse:collapse}} td,th{{padding:7px;border-bottom:1px solid #26313b;text-align:left}}
.grid{{position:relative;height:330px;background:linear-gradient(#17212b 1px,transparent 1px),linear-gradient(90deg,#17212b 1px,transparent 1px);background-size:22px 22px}}
.pin{{position:absolute;padding:5px 7px;border-radius:6px;background:#243444;font-size:11px;transform:translate(-50%,-50%)}}
.robot{{border:1px solid #8da0b2}} .station{{border:1px dashed #778696}}
.event{{padding:5px 0;border-bottom:1px solid #26313b}}
.metric{{font-size:24px}}
@media(max-width:800px){{main{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header><div><strong>AUTONOMOUS MICROFACTORY OS</strong><div style="font-size:12px;color:#93a4b3">factory orchestration / fleet / vision / replay</div></div><span class="badge">SIMULATION PREVIEW</span></header>
<main>
<section class="card"><h3>Factory map</h3><div class="grid" id="grid"></div></section>
<section class="card"><h3>System</h3><div id="health">checking...</div><p><span class="metric" id="jobCount">0</span> jobs · <span class="metric" id="robotCount">0</span> robots</p><h3>Events</h3><div id="events"></div></section>
<section class="card"><h3>Jobs</h3><table><thead><tr><th>ID</th><th>State</th><th>Stage</th></tr></thead><tbody id="jobs"></tbody></table></section>
<section class="card"><h3>Robots</h3><table><thead><tr><th>ID</th><th>State</th><th>Battery</th></tr></thead><tbody id="robots"></tbody></table></section>
</main>
<script>
const preview={payload};
async function load(){{
 let data=preview;
 try{{let r=await fetch('/demo/snapshot'); if(r.ok)data=await r.json();}}catch(e){{}}
 document.getElementById('jobCount').textContent=data.jobs.length;
 document.getElementById('robotCount').textContent=data.robots.length;
 document.getElementById('jobs').innerHTML=data.jobs.map(j=>`<tr><td>${{j.id}}</td><td>${{j.state}}</td><td>${{j.stage}}</td></tr>`).join('');
 document.getElementById('robots').innerHTML=data.robots.map(r=>`<tr><td>${{r.id}}</td><td>${{r.state}}</td><td>${{r.battery}}%</td></tr>`).join('');
 document.getElementById('events').innerHTML=data.events.map(e=>`<div class="event">t=${{e.tick}} · ${{e.text}}</div>`).join('');
 document.getElementById('grid').innerHTML=[...data.stations.map(s=>`<div class="pin station" style="left:${{5+s.x*5}}%;top:${{8+s.y*10}}%">${{s.id}}<br>${{s.state}}</div>`),...data.robots.map(r=>`<div class="pin robot" style="left:${{5+r.x*5}}%;top:${{8+r.y*10}}%">${{r.id}}<br>${{r.state}}</div>`)].join('');
 try{{let h=await fetch('/healthz'); document.getElementById('health').textContent=h.ok?'factory-api HEALTHY':'health unavailable';}}catch(e){{document.getElementById('health').textContent='preview mode';}}
}}
load();
</script>
</body></html>"""
