# Project

**Name:** Autonomous Microfactory OS

**Problem:** Coordinate a simulated electronics-style microfactory containing autonomous movers, machines, vision stations and shared resources. The platform must accept jobs, plan/schedule work, route movers without collisions, execute commands through a typed runtime boundary, observe every important action and reproduce failures.

**Primary portfolio signal:** software engineering for robotics at system scale, not a tutorial robot demo.

## Non-goals for the first release
- safety certification
- physical production deployment
- bespoke real-time motor-control firmware
- photorealistic simulation
- autonomous LLM actuation without deterministic safety gates

## Existing related repositories
- `sri1650/ros2-autonomous-warehouse-robot`
- `sri1650/ros2-vision-guided-manipulator`

This project should reuse concepts, not copy their architecture. It demonstrates factory orchestration and distributed robotics infrastructure.
