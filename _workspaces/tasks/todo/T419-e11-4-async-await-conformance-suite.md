---
id: T419
title: E11.4 — Async/await, Future layout & cancellation conformance suite
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T415, T416, T417, T088, T418]
priority: 142
status: todo
attempts: 0
paths: [tests/conformance/p11/e11_4_async]
spec: [spec/SPEC-33-async.md, 0093, 0127, 0135, 0201, 0202, 0248, tasks/0275, tasks/0297, tasks/0619]
covers: [REQ-ASY-010, REQ-ASY-011, REQ-ASY-064, REQ-ASY-065, REQ-ASY-070, REQ-ASY-075, REQ-ASY-077, REQ-ASY-078, REQ-ASY-079, REQ-ASY-080, REQ-ASY-081, REQ-ASY-082, REQ-ASY-083, REQ-ASY-133, REQ-ASY-134, REQ-ASY-142]
---
# T419 — E11.4 — Async/await, Future layout & cancellation conformance suite

## Goal
Verify the `E11.4` exit criterion ('async conformance') across all `AXS-ASY-*` rules and `AASYNC-*` invariants in `[interp]`, `[native]`, and `[native-O1]` modes.

## Scope
- Create `tests/conformance/p11/e11_4_async/` testing `async fn` state-machine lowering, multi-await chains, loops/branches with `.await`, `?` early return across `.await`, generic and trait `async fn`, deterministic Drop order on completion vs mid-flight cancellation, zero-heap stack polling via `block_on`, and negative `ui` checks for `view`/`mut_view`/`MutexGuard` across `.await` and `Future: Send` bounds.

## Acceptance
- [ ] All tests in `tests/conformance/p11/e11_4_async/` pass in `[interp]`, `[native]`, and `[native-O1]` under `axiomc2.exe` (`WEAK-NATIVE 0`, `0 FAIL`).
- [ ] Full test suite passes in `build-snap-T419` under `axiomc2.exe`; `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T419-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or std source files.

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T419/build` and `python tools/axtest.py --compiler build-snap-T419/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
