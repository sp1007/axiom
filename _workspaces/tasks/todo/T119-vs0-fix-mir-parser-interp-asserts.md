---
id: T119
title: VS0 fix: text parser bit-not, overflows, and interp arithmetic
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T116]
priority: 11
status: blocked
attempts: 1
paths: [tests/conformance/vs0]
locks: [bootstrap/axiom0/src/interp/interp.c, bootstrap/axiom0/src/mir/parse.c]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-00-bootstrap.md, spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md, spec/decisions/ADR-0016-vs0-gate-fix-tasks.md, spec/decisions/ADR-0017-checked-arithmetic-mir.md]
covers: [REQ-EXP-021]
started: 2026-10-07 18:33:13
unblocks: 1
unblock_failures: 0
---
# T119 — VS0 fix: text parser bit-not, overflows, and interp arithmetic

## Goal
The THIR->MIR builder emits the MIR SPEC-03 / FP-03 prescribes — correct operators and explicit Assert terminators for every trapping operation — so the oracle and later the native backend (T023, AXS-BOOT-007) see the checks in MIR. Fix task created by the T022 unblock (ADR-0016); bugs M1-M3 of _workspaces/reports/T022-report.md.

## Scope
- parse.c: Add support for bitwise NOT ~ operator in the MIR text parser.
- parse.c: Add support for the new overflows(...) rvalue in the MIR text parser.
- interp.c: Implement OverflowsBinaryOp accurately using __builtin_*_overflow checks (including for large 32-bit unsigned additions). Fix the 32-bit unsigned overflow false panics caused by incorrectly using int32_t.

## Acceptance
- [ ] `tests/mir/build` goldens (regenerated FP-03 + new ones) pass and verify.
- [ ] In a snapshot with T022's suite present, `seam_bitnot_value` no longer fails in MIR.
- [ ] An ICE test (or C unit test) shows an unhandled kind is reported, not dropped.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T119-report.md` with exact `## Files changed`.

## Out of scope
- Interpreter value model and panic format (T117); parser (T114); typeck (T115).
  Do not edit `tests/conformance/vs0`.

## Notes
- T117 depends on this task and holds `bootstrap/axiom0/src/interp` as its path; the lock here only
  covers the terminator dispatch.

## Log
- 2026-10-06 23:44:40 started (attempt 1) T116-impl
- 2026-10-07 07:50:23 requeue: quota 429 (infrastructure failure: attempt refunded)
- 2026-10-07 08:37:13 started (attempt 1) T116-impl
- 2026-10-07 09:22:27 block: Missing CheckedBinaryOp in MIR, and no clear way to represent checked arithmetic without tuple support in the interpreter.
- 2026-10-07 09:25:56 unblocked (cycle 1) 
- 2026-10-07 10:01:32 started (attempt 1) T116-impl
- 2026-10-07 10:19:20 block: Interferes with T118
- 2026-10-07 11:05:06 block: QA failed 3 times: path conflict on control_flow files with T114
- 2026-10-07 11:05:43 unblocked (cycle 2) 
- 2026-10-07 11:21:07 started (attempt 1) T116-impl
- 2026-10-07 18:29:40 block: QA failed 3 times: archcheck violation, dummy OverflowsBinaryOp, base.c path violation
- 2026-10-07 18:29:40 parked: unblock cap reached (unblocks=2, failed unblock agents=0); needs the owner
- 2026-10-07 18:30:34 unblocked (owner-approved cycle 0) 
- 2026-10-07 18:30:34 started (attempt 1) 
- 2026-10-07 18:30:52 block: QA failed 3 times: archcheck violation, dummy OverflowsBinaryOp, base.c path violation
- 2026-10-07 18:31:51 unblocked (cycle 1) 
- 2026-10-07 18:33:13 started (attempt 1) T116-impl
- 2026-10-07 19:53:32 block: QA failed 3 times: false panics for large u32 addition, parse.c lacks ~, parse.c lacks overflows
