from __future__ import annotations
import json


def demo_replay():
    frames=[
        {"index":0,"tick":0,"summary":"WORLD_INITIALIZED · world","states":{"printer-1":"READY","vision-1":"READY"}},
        {"index":1,"tick":10,"summary":"MACHINE_STARTED · printer-1 · print-104","states":{"printer-1":"BUSY","vision-1":"READY"}},
        {"index":2,"tick":18,"summary":"MACHINE_SUCCEEDED · printer-1 · print-104","states":{"printer-1":"READY","vision-1":"READY"}},
        {"index":3,"tick":20,"summary":"MACHINE_STARTED · vision-1 · inspect-104","states":{"printer-1":"READY","vision-1":"BUSY"}},
        {"index":4,"tick":22,"summary":"MACHINE_FAILED · vision-1 · inspect-104","states":{"printer-1":"READY","vision-1":"FAULTED"}},
        {"index":5,"tick":23,"summary":"RETRY_REQUESTED · inspect-104","states":{"printer-1":"READY","vision-1":"RECOVERING"}},
        {"index":6,"tick":26,"summary":"MACHINE_STARTED · vision-1 · inspect-104 attempt=2","states":{"printer-1":"READY","vision-1":"BUSY"}},
        {"index":7,"tick":28,"summary":"MACHINE_SUCCEEDED · vision-1 · inspect-104","states":{"printer-1":"READY","vision-1":"READY"}},
        {"index":8,"tick":29,"summary":"SCENARIO_COMPLETE · world","states":{"printer-1":"READY","vision-1":"READY"}},
    ]
    return {"mode":"simulation-preview","frames":frames}


def time_machine_html():
    payload=json.dumps(demo_replay())
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Microfactory Time Machine</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{margin:0;background:#0b1016;color:#dbe5ee;font-family:ui-monospace,monospace}}
main{{max-width:900px;margin:auto;padding:24px}} .card{{border:1px solid #293440;background:#111923;border-radius:10px;padding:18px;margin:14px 0}}
input{{width:100%}} .state{{display:inline-block;margin:5px;padding:7px 9px;border:1px solid #4a5b6c;border-radius:7px}}
.badge{{font-size:12px;border:1px solid #4a5b6c;padding:3px 7px;border-radius:999px}}
h1{{margin-bottom:5px}} .muted{{color:#92a3b2}}
</style></head><body><main>
<h1>Factory Time Machine</h1><div class="muted">deterministic replay / causal failure inspection <span class="badge">SIMULATION PREVIEW</span></div>
<div class="card"><input id="slider" type="range" min="0" max="0" value="0"><p>Frame <b id="idx"></b> · Tick <b id="tick"></b></p><h3 id="summary"></h3><div id="states"></div></div>
<div class="card"><h3>Why this exists</h3><p>Failures should be reproducible. The production integration will replace this preview stream with persisted deterministic events and trace correlation.</p></div>
<script>
const preview={payload};
async function start(){{
 let data=preview; try{{let r=await fetch('/demo/replay');if(r.ok)data=await r.json();}}catch(e){{}}
 const s=document.getElementById('slider'); s.max=data.frames.length-1;
 function render(){{
   const f=data.frames[Number(s.value)];
   idx.textContent=f.index; tick.textContent=f.tick; summary.textContent=f.summary;
   states.innerHTML=Object.entries(f.states).map(([k,v])=>`<span class="state">${{k}} · ${{v}}</span>`).join('');
 }}
 s.oninput=render; render();
}}
start();
</script></main></body></html>"""
