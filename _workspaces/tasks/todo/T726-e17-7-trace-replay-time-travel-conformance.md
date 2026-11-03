---
id: T726
title: E17.7 AXREPLAY deterministic execution recording, replay & time-travel debugging conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T217, T316, T725]
priority: 197
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_7_trace_replay]
spec: [spec/SPEC-98-trace-replay.md, 0147, tasks/1058, tasks/0694]
covers: [REQ-DBG-116, REQ-DBG-121]
---
# T726 — E17.7 AXREPLAY deterministic execution recording, replay & time-travel debugging conformance suite

## Goal
Certify the E17.7 exit criteria: deterministic AXREPLAY recording and replay across concurrency/clock/RNG/IO boundaries, crash reproduction, time-travel queries, and zero disabled overhead.

## Scope
- Create `tests/conformance/p17/e17_7_trace_replay` covering:
-   - Zero runtime/codegen overhead when `--trace` is disabled (`0147 §20`).
-   - Bit-exact deterministic replay of programs using monotonic/wall clocks, RNG, file I/O, FFI callbacks, and concurrent thread/async task schedules across 10+ replay runs.
-   - Crash/panic reproduction from a recorded `.axtrace` file and exact `reverse-step`, `reverse-continue`, and watchpoint `last-writer` source-mapped queries.
-   - Negative divergence test verifying `AXREPLAY_DIVERGENCE` when replaying a trace against a mismatched binary.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p17/e17_7_trace_replay` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T726-report.md` with exact `## Files changed`.

## Out of scope
- Phase P17 gate certification (`T317`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
