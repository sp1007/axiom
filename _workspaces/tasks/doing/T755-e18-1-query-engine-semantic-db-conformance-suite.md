---
id: T755
title: E18.1 — Query engine, cycle recovery & semantic database conformance suite
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T754]
priority: 705
status: doing
attempts: 1
paths: [tests/conformance/p18/e18_1_query_engine]
spec: [spec/SPEC-21-query-engine-semantic-db.md, tasks/0384, tasks/0530, tasks/0533, tasks/0781, tasks/0791]
covers: [REQ-LNK-1384, REQ-LNK-1385, REQ-LNK-1386, REQ-LNK-1387, REQ-LNK-1388, REQ-LNK-1389, REQ-LNK-1390, REQ-LNK-1391, REQ-LNK-1392, REQ-LNK-1393, REQ-LNK-1394, REQ-LNK-1395, REQ-LNK-1396, REQ-LNK-1397, REQ-LNK-1398, REQ-LNK-1399, REQ-LNK-1400, REQ-LNK-1401, REQ-LNK-1402, REQ-LNK-1403, REQ-LNK-1404, REQ-LNK-1405, REQ-LNK-1406, REQ-LNK-1407, REQ-LNK-1408, REQ-LNK-1409, REQ-LNK-1410, REQ-LNK-1411, REQ-LNK-1412, REQ-LNK-1413, REQ-LNK-1414, REQ-LNK-1415, REQ-LNK-1416, REQ-LNK-1417, REQ-LNK-1418, REQ-LNK-1419, REQ-LNK-1420, REQ-LNK-1421, REQ-LNK-1422, REQ-LNK-1423, REQ-LNK-1424, REQ-LNK-1425, REQ-LNK-1426, REQ-LNK-1427, REQ-LNK-1428, REQ-LNK-1429, REQ-LNK-1430, REQ-LNK-1431, REQ-LNK-1432, REQ-LNK-1433]
started: 2026-11-07 19:12:32
agent: T755-impl
---
# T755 — E18.1 — Query engine, cycle recovery & semantic database conformance suite

## Goal
Certify E18.1 exit criteria with an end-to-end conformance suite covering demand-driven `CompilerDB` queries, memoization, deterministic cycle detection/recovery, snapshot-bound diagnostics, and revision invalidation.

## Scope
- Create conformance tests in `tests/conformance/p18/e18_1_query_engine` verifying:
  - demand-driven query isolation across multi-module programs;
  - canonical cycle diagnostics regardless of query invocation order;
  - identical diagnostic sets and semantic results between cold evaluation and warm memoized evaluation (`tasks/0791`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p18/e18_1_query_engine` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T755-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T755/build` and `python tools/axtest.py --compiler build-snap-T755/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:56:00 created by T218 (P18 phase planning)
- 2026-11-07 19:12:32 started (attempt 1) T755-impl
