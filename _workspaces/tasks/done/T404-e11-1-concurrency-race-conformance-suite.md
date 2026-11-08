---
id: T404
title: E11.1 — Concurrency & data-race conformance suite
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T400, T089, T401, T402, T403]
priority: 125
status: done
attempts: 1
paths: [tests/conformance/p11/e11_1_concurrency]
spec: [spec/SPEC-30-concurrency.md, 0079, 0091, 0105, 0126, 0136, tasks/0298, tasks/0488, tasks/0685]
covers: [REQ-CONC-016, REQ-CONC-018, REQ-CONC-085, REQ-CONC-086, REQ-CONC-087, REQ-CONC-089, REQ-CONC-094, REQ-CONC-158, REQ-CONC-159, REQ-CONC-160, REQ-CONC-161, REQ-CONC-162, REQ-CONC-163, REQ-CONC-164, REQ-CONC-176, REQ-CONC-181, REQ-CONC-182, REQ-CONC-183, REQ-CONC-192, REQ-CONC-193, REQ-CONC-197, REQ-CONC-202, REQ-CONC-203, REQ-CONC-204, REQ-CONC-205, REQ-CONC-206, REQ-CONC-207]
started: 2026-11-08 10:59:48
finished: 2026-11-08 12:15:06
---
# T404 — E11.1 — Concurrency & data-race conformance suite

## Goal
Verify the `E11.1` exit criterion ('race conformance suite green') with an exhaustive positive and negative concurrency conformance suite mapped to `SPEC-30` rule IDs.

## Scope
- Create `tests/conformance/p11/e11_1_concurrency/` covering every `AXS-CONC-*` rule and `ACONC-*`/`ACONCUR-*` invariant.
- Include negative `ui` tests for `Send != Share`, `!Send` raw pointers/handles across `spawn`, `!Share` interior-mutable types across threads, escaping `view`/`mut_view` captures, `READ/WRITE` and `WRITE/WRITE` race patterns, and unsynchronized mutable statics.
- Include positive `run` tests (`modes: interp native`, checking `-O0` and `-O1`) for `Send` ownership transfer, `Share` concurrent read views, disjoint struct field mutation, and happens-before ordering.

## Acceptance
- [ ] All tests in `tests/conformance/p11/e11_1_concurrency/` pass under `axiomc2.exe` (`WEAK-NATIVE 0`, `0 FAIL`).
- [ ] Full test suite passes in `build-snap-T404` under `axiomc2.exe`; `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T404-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or standard library source files.

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T404/build` and `python tools/axtest.py --compiler build-snap-T404/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-08 10:59:48 started (attempt 1) T404-impl
- 2026-11-08 12:15:06 accepted by QA -> done
