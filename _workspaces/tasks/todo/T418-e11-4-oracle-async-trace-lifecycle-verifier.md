---
id: T418
title: E11.4 — Oracle deterministic async trace & lifecycle verifier
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T088]
priority: 141
status: todo
attempts: 0
paths: [tests/run/async/oracle_trace, tests/ui/async/lifecycle]
locks: [compiler/interp/oracle.ax, compiler/interp/interp.ax, compiler/interp_opt/session.ax, compiler/driver/opts.ax, compiler/driver/pipeline.ax, tests/selfhost]
spec: [spec/SPEC-33-async.md, 0093, 0127, 0135, 0202, tasks/0275, tasks/0297, tasks/0619]
covers: [REQ-ASY-007, REQ-ASY-009, REQ-ASY-013, REQ-ASY-014, REQ-ASY-016, REQ-ASY-017, REQ-ASY-018, REQ-ASY-020, REQ-ASY-021, REQ-ASY-032, REQ-ASY-034, REQ-ASY-038, REQ-ASY-043, REQ-ASY-046, REQ-ASY-047, REQ-ASY-052, REQ-ASY-056, REQ-ASY-057, REQ-ASY-058, REQ-ASY-059, REQ-ASY-063, REQ-ASY-066, REQ-ASY-073, REQ-ASY-074, REQ-ASY-088, REQ-ASY-093, REQ-ASY-096, REQ-ASY-098, REQ-ASY-099, REQ-ASY-101, REQ-ASY-110, REQ-ASY-111, REQ-ASY-112, REQ-ASY-113, REQ-ASY-114, REQ-ASY-115, REQ-ASY-121, REQ-ASY-131, REQ-ASY-132, REQ-ASY-136, REQ-ASY-140, REQ-ASY-143, REQ-ASY-148]
---
# T418 — E11.4 — Oracle deterministic async trace & lifecycle verifier

## Goal
Equip the MIR interpreter oracle (`compiler/interp`) and `inspect` command with deterministic async lifecycle tracing (`POLL`, `SUSPEND`, `RESUME`, `WAKE`, `COMPLETE`, `CANCEL_DROP`) and Future state-size inspection (`REQ-ASY-045, 059, 060`).

## Scope
- Record and verify observable async lifecycle trace events (`POLL`, `SUSPEND`, `RESUME`, `WAKE`, `COMPLETE`, `CANCEL_DROP`) in `compiler/interp/oracle.ax` and `compiler/interp/interp.ax` (`REQ-ASY-059, 060`).
- Verify in the oracle and natively that polling a completed or cancelled `Future` panics deterministically, dropping a `Pending` Future runs only the active state's live-field destructors in reverse declaration order without leaking or double-dropping (`REQ-ASY-034, 052`), and stack-allocated Futures execute with zero heap allocations (`REQ-ASY-016, 021, 046`).
- Support `inspect --emit=async-layout` (or state-machine layout annotations in `inspect --emit=mir`) reporting the state count, byte size, alignment, and live fields per suspension state of each `async fn` (`REQ-ASY-045`).

## Acceptance
- [ ] `tests/run/async/oracle_trace/*.ax` (`modes: interp native`) verifies multi-step suspend/resume trace order, early-drop cancellation cleanup of nested futures, zero-heap execution of stack futures, and state-size layout inspection.
- [ ] `tests/ui/async/lifecycle/*.ax` verifies poll-after-completion panic and invalid state transitions.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T418` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T418-report.md` with exact `## Files changed`.

## Out of scope
- Multi-threaded work-stealing executors (`T421`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T418/build` and `python tools/axtest.py --compiler build-snap-T418/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
