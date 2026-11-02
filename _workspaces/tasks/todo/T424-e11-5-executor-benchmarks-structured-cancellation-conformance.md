---
id: T424
title: E11.5 — Executor benchmarks, fiber & structured-cancellation conformance suite
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T420, T421, T422, T423]
priority: 147
status: todo
attempts: 0
paths: [tests/conformance/p11/e11_5_executors, tests/perf/p11_executor]
spec: [spec/SPEC-34-executors-fibers.md, 0202, 0204, 0205, tasks/0277, tasks/0278, tasks/0620, tasks/0836]
covers: [REQ-ASY-165]
---
# T424 — E11.5 — Executor benchmarks, fiber & structured-cancellation conformance suite

## Goal
Verify the `E11.5` exit criterion ('executor benchmarks + structured-cancellation tests') across `LocalExecutor`, work-stealing `Executor`, `TaskGroup`, and `Fiber`.

## Scope
- Create `tests/conformance/p11/e11_5_executors/` covering structured task cancellation trees, sibling failure cancellation, `AsyncMutex` cancellation safety (next waiter wakes when cancelled waiter drops), `spawn_local` thread-affinity pinning vs `spawn` work-stealing migration, and `Fiber` context-switching conformance.
- Create `tests/perf/p11_executor/` measuring single-thread task spawn/poll throughput, multi-thread work-stealing fan-out/fan-in latency, async channel ping-pong throughput, and `Fiber` context-switch overhead.

## Acceptance
- [ ] All tests in `tests/conformance/p11/e11_5_executors/` and `tests/perf/p11_executor/` pass in `[interp]`, `[native]`, and `[native-O1]` under `axiomc2.exe` (`WEAK-NATIVE 0`, `0 FAIL`).
- [ ] Full test suite passes in `build-snap-T424` under `axiomc2.exe`; `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T424-report.md` with exact `## Files changed` and benchmark numbers.

## Out of scope
- Modifying compiler or std source files.

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T424/build` and `python tools/axtest.py --compiler build-snap-T424/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
