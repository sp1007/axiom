---
id: T491
title: Fix stage-1 axiomc1 access violation (0xC0000005) on 2 parity programs (axiomc_e2e.test baseline)
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T164]
priority: 12
status: todo
attempts: 0
paths: [tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py, tests/run/parity/backend, _workspaces/baseline-failures.txt]
locks: []
spec: [spec/SPEC-20-selfhost.md, spec/SPEC-00-bootstrap.md]
covers: [REQ-BLD-028]
---
# T491 — Stage-1 axiomc1 crashes on two parity programs

## Why
`selfhost/obj_link_driver/axiomc_e2e.test` fails at HEAD (T481a and T485 gates): the stage-1 compiler `axiomc1.exe`
(built by the frozen axiom0) crashes with 0xC0000005 on `tests/run/parity/backend/const_table_str.ax` and
`tests/run/parity/backend/qa_narrow_const_repeat_and_print_int_edges.ax` (`axiomc1 inspect --emit=thir` too), while
stage-2 `axiomc2` handles both (rc 0). Stage 1 is the trust root of the bootstrap: a crash there means either axiom0
miscompiles part of axiomc or axiomc has undefined behaviour that only shows under axiom0's code generation.

## Scope
- Diagnose (debugger / stack-trace sampler / bisect the source of the two programs to a minimal trigger). Decide:
  (a) bug in axiomc source (UB, uninitialised read, out-of-bounds) → fix it in `compiler/` (extend `paths` via the
  report; the orchestrator re-scopes), (b) axiom0 miscompile → report BLOCKED with the minimal repro so the architect
  creates an `AX0-FIX` task (axiom0 is frozen; this task must not edit `bootstrap/axiom0`).
- Keep both programs in the parity set; add the minimal trigger as a regression test.
- Remove `selfhost/obj_link_driver/axiomc_e2e.test` from `_workspaces/baseline-failures.txt` when it passes.

## Acceptance
- [ ] `axiomc_e2e.test` passes; both programs compile with axiomc1 and axiomc2 with identical output.
- [ ] Normal gate; fixed point holds. Report `_workspaces/reports/T491-report.md` with exact `## Files changed`.

## Log
- 2026-11-18 created by orchestrator (T485 gate follow-up F-4)
