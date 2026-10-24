# Capability-to-Portfolio Mapping

| Capability to prove | Project evidence planned |
|---|---|
| Large robotics software architecture | Bounded contexts, typed contracts, state ownership, integration tests |
| Python + systems language | Python orchestration/optimisation + Rust runtime |
| Robot/camera/tool/job abstractions | Domain contracts and simulator adapters |
| Multi-robot coordination | temporal reservation planner, Cooperative A*, later CBS benchmark |
| Scheduling/optimisation | FIFO baseline + OR-Tools CP-SAT benchmark |
| Vision in control loop | alignment + pick/placement verification with ONNX boundary |
| High-level to low-level control bridge | Protobuf/gRPC Python -> Rust command gateway |
| Simulation, tracing, replay | deterministic simulator + OTel + ClickHouse + replay tool |
| Production engineering | CI, typed interfaces, fault injection, idempotency, telemetry |
| Agentic robotics | constrained diagnostic agent + synthetic eval suite |

## Interview narrative
1. Start from the factory problem and explicit ownership boundaries.
2. Explain why Python and Rust are split at the runtime boundary.
3. Show a job trace across scheduler, fleet, runtime and vision.
4. Reproduce a failure from stored events.
5. Benchmark the baseline planner/scheduler against the improved algorithm.
6. State limitations and hardware-validation status precisely.
