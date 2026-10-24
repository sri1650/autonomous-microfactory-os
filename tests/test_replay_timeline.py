from microfactory.replay.timeline import build_timeline
from microfactory.sim.events import SimEvent

def test_timeline_tracks_machine_state():
    events=[
        SimEvent(0,0,"WORLD_INITIALIZED","world",{}),
        SimEvent(1,1,"MACHINE_STARTED","m1",{"task_id":"t1"}),
        SimEvent(2,2,"MACHINE_SUCCEEDED","m1",{"task_id":"t1"}),
        SimEvent(3,3,"SCENARIO_COMPLETE","world",{}),
    ]
    frames=build_timeline(events)
    assert frames[1].machine_states["m1"]=="BUSY"
    assert frames[2].machine_states["m1"]=="READY"
