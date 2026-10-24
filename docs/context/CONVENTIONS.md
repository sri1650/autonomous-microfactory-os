# Conventions

## Python
- Python 3.12 target
- `src/` layout
- type hints required on public functions
- domain layer cannot import FastAPI, SQLAlchemy or vendor SDKs
- pytest tests use Arrange/Act/Assert structure
- deterministic algorithms accept a seed when randomness exists

## Rust
- stable edition 2021 initially
- no `unwrap()`/`expect()` in runtime command paths except tests
- state transitions live in pure functions/types where possible
- public protocol types derive/convert explicitly; avoid stringly typed state

## Naming
- snake_case Python modules/functions
- PascalCase Python/Rust types
- command IDs are UUID-like opaque strings
- event names use `<context>.<entity>.<event>` if serialized

## Git
- small commits matching one task
- commit prefix: `feat:`, `fix:`, `test:`, `docs:`, `chore:`
- no generated binaries or large datasets in Git

## Evidence language
Use: implemented, unit-tested, integration-tested, simulation-validated, hardware-validated. Do not upgrade the evidence level without proof.
