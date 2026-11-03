---
id: T602
title: E15.1 — Optimization pass manager, effect/proof summaries & transformation contract verifier
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T601]
priority: 95
status: doing
attempts: 1
paths: [compiler/opt/passmgr, compiler/opt/effects, tests/run/opt_passmgr]
locks: [compiler/opt/mod.ax, compiler/opt/optir/mod.ax, tests/selfhost/opt]
spec: [spec/SPEC-70-optir-ssa-memoryssa.md, tasks/0399, tasks/0438, tasks/0443, tasks/0447, tasks/0474, tasks/0480, tasks/0487, tasks/0545, tasks/0546, tasks/0579, tasks/0795, tasks/0797]
covers: [REQ-CORE-447, REQ-VER-027, REQ-OPT-060, REQ-OPT-061, REQ-OPT-062, REQ-OPT-063, REQ-OPT-064, REQ-OPT-065, REQ-OPT-348, REQ-OPT-349, REQ-OPT-350, REQ-OPT-355, REQ-OPT-356, REQ-OPT-373, REQ-OPT-374, REQ-OPT-393, REQ-OPT-394, REQ-OPT-395, REQ-OPT-396, REQ-OPT-404, REQ-OPT-405, REQ-OPT-406]
started: 2026-11-03 22:52:04
agent: T602-impl
---
# T602 — E15.1 — Optimization pass manager, effect/proof summaries & transformation contract verifier

## Goal
Implement the `OptIR` Pass Manager, canonical `EffectInfo` inference engine, analysis dependency/invalidation tracker, and transformation contract verifier in `compiler/opt/passmgr` and `compiler/opt/effects` per `spec/SPEC-70-optir-ssa-memoryssa.md`.

## Scope
- Implement `PassManager` (`compiler/opt/passmgr`) tracking explicit pass dependencies, required analyses (`DominatorTree`, `MemorySSA`, `EffectInfo`, `AliasInfo`, `EscapeInfo`, `RangeInfo`), preserved analyses, and invalidated analyses (`REQ-CORE-447`, `REQ-OPT-350`, `REQ-OPT-356`, `REQ-OPT-373`, `REQ-OPT-374`).
- Implement canonical, deterministic, conservative `EffectInfo` inference (`compiler/opt/effects`) over MIR/`OptIR` and call summaries (`Pure`, `ReadsMemory`, `WritesMemory`, `MayPanic`, `Allocates`, `IO`, `Atomic`, `Volatile`, `FFI`, `Unknown` — `REQ-OPT-348`, `REQ-OPT-349`, `REQ-OPT-393..396`, `REQ-VER-027`), guaranteeing `Unknown` is never treated as `Pure`.
- Implement the transformation contract & proof verifier (`REQ-OPT-060..065`, `REQ-OPT-404..406`) that checks pass preconditions, proof provenance, and postconditions under `--verify-each` and rejects any transformation whose proof fails closed.

## Acceptance
- [ ] Run tests in `tests/run/opt_passmgr` verify analysis caching/invalidation, `EffectInfo` summary propagation (preserving I/O, atomic, `volatile`, and panic effects), and `--verify-each` transformation contract checking across `-O0`, `-O1`, and `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T602-report.md` with exact `## Files changed`.

## Out of scope
- Concrete scalar optimization passes (`T603`) and alias/escape passes (`T606`–`T607`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T602/build` and `python tools/axtest.py --compiler build-snap-T602/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:38:00 created by T215 (P15 phase planning)
- 2026-11-03 12:16:28 started (attempt 1) 
- 2026-11-03 22:51:47 requeue: restart (not charged: attempt refunded)
- 2026-11-03 22:52:04 started (attempt 1) T602-impl
