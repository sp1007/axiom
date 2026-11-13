---
id: T311
title: Phase P11 gate — Concurrency & async
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T211, T088, T089, T090, T400, T401, T402, T403, T404, T405, T406, T407, T408, T409, T410, T411, T412, T413, T414, T415, T416, T417, T418, T419, T420, T421, T422, T423, T424, T425, T426, T427, T428, T429, T434, T435, T436, T430, T431, T432, T433, T438, T439, T440, T441, T442, T443, T444, T445, T446, T447, T448, T449, T421a, T422a, T422b, T422c]
priority: 311
status: todo
attempts: 0
paths: [tests/conformance/p11, _workspaces/reports/phase-P11-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-30-concurrency.md, spec/SPEC-31-atomics.md, spec/SPEC-32-threads-sync.md, spec/SPEC-33-async.md, spec/SPEC-34-executors-fibers.md, spec/SPEC-35-async-io.md]
covers: [REQ-ASY-167, REQ-ASY-168]
---
# T311 — Phase P11 gate: Concurrency & async

## Goal
Certify that phase P11 meets the exit criteria of every epic (`E11.1`–`E11.6`) in `spec/ROADMAP.md` §3 and that all 421 requirements mapped to the phase (`T088`–`T090`, `T400`–`T428`) are implemented and verified under both the MIR interpreter oracle and native Windows x86-64 execution.

## Scope
- Run the full suite on `axiomc2.exe` (`--exclude-requires axiom0-internal`) and run each P11 epic's exit-criterion conformance suite (`tests/conformance/p11/e11_1_concurrency` through `tests/conformance/p11/e11_6_async_io` and `tests/perf/p11_executor`).
- Verify `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P11-concurrency-async` and `reqcov.py --strict`: every requirement mapped to P11 is implemented (`done`) with 0 gaps and 0 problems.
- Collect the phase conformance summary into `tests/conformance/p11/` and write the phase review `_workspaces/reports/phase-P11-review.md` (starting with a Vietnamese `## Tóm tắt` section).

## Acceptance
- [ ] Every epic exit criterion (`E11.1` race conformance, `E11.2` atomic litmus under oracle + native stress, `E11.3` native thread/sync stress, `E11.4` async conformance, `E11.5` executor benchmarks + structured cancellation, `E11.6` async file/socket tests) is demonstrated with commands and results in the QA report.
- [ ] Full suite green under `axiomc2.exe` (`0 FAIL`, `WEAK-NATIVE 0` on all P11 tests; gate rule R9: PASS or BLOCKED); `reqcov.py --strict`, `harness_check.py`, and `archcheck.py` exit 0.
- [ ] `_workspaces/reports/phase-P11-review.md` and `_workspaces/reports/T311-report.md` written with exact `## Files changed`.

## Out of scope
- Implementing new features; any defect discovered by the gate is filed as a follow-up task by the architect.

## Notes
- Depends on planning task `T211`, original P11 tasks `T088`–`T090`, and all expanded P11 tasks `T400`–`T428` (32 implementation/spec/conformance tasks across `E11.1`–`E11.6`).

## Log
- 2026-10-06 02:23:54 covers += REQ-ASY-167, REQ-ASY-168 (metadata only)
- 2026-11-03 00:10:00 updated depends to include T400-T428 in T211 (P11 phase planning)
- 2026-11-13 07:40:00 depends += T434, T435, T436, T430, T431, T432, T433 (ADR-0041 baseline fix tasks; the phase gate runs `--no-cache` and needs an empty-or-admitted baseline)
