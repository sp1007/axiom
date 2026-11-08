---
id: T408
title: E11.2 — Oracle atomic memory model & deterministic schedule explorer
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T406]
priority: 129
status: done
attempts: 1
paths: [compiler/interp, tests/run/concurrency/atomics_oracle]
locks: [compiler/interp_opt/session.ax, compiler/driver/opts.ax, compiler/driver/pipeline.ax, tests/selfhost]
spec: [spec/SPEC-31-atomics.md, 0033, 0092, 0128, 0208, tasks/0328, tasks/0515]
covers: [REQ-CONC-054, REQ-ATM-006, REQ-ATM-007, REQ-ATM-008, REQ-ATM-010, REQ-ATM-012, REQ-ATM-013, REQ-ATM-018, REQ-ATM-019, REQ-ATM-021, REQ-ATM-026, REQ-ATM-032]
started: 2026-11-08 16:40:05
finished: 2026-11-08 19:19:30
---
# T408 — E11.2 — Oracle atomic memory model & deterministic schedule explorer

## Goal
Implement `Atomic` execution, per-location modification order, Acquire/Release vector-clock tracking, and deterministic schedule exploration in the MIR interpreter oracle (`compiler/interp`).

## Scope
- Execute MIR `Atomic` statements (`Load`, `Store`, `Rmw`, `CmpXchg`, `Fence`) in `compiler/interp/interp.ax` and `compiler/interp/oracle.ax`.
- Maintain per-atomic-location modification order, `Release`/`Acquire` synchronizes-with vector clocks, and a global `SeqCst` total order so the oracle validates happens-before visibility and flags any concurrent ordinary read/write racing with an atomic or ordinary access (`AX_UNSAFE_INTERP_UB`, exit 125).
- Support deterministic schedule exploration across concurrent oracle execution contexts (controlled by deterministic seed/interleaving points around atomic operations) and deterministic spurious failure simulation for `compare_exchange_weak`.

## Acceptance
- [ ] `tests/run/concurrency/atomics_oracle/*.ax` (`modes: interp native` where applicable, plus oracle race-detection tests expecting exit 125) verifies Acquire/Release publication, `SeqCst` ordering, `compare_exchange_weak` retry loops, wrapping RMW semantics, and detection of unsynchronized ordinary-memory races.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T408` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T408-report.md` with exact `## Files changed`.

## Out of scope
- OS thread creation (handled in `T090`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T408/build` and `python tools/axtest.py --compiler build-snap-T408/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-08 16:40:05 started (attempt 1) T408-impl
- 2026-11-08 19:19:30 accepted by QA -> done
