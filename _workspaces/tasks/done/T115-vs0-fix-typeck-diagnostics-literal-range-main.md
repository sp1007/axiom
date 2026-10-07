---
id: T115
title: VS0 fix: typeck diagnostics, literal range, float rejection, main signature in check
phase: P3-semantic-core
owner: axiom-frontend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T021]
priority: 11
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types, tests/typeck, tests/ui/typeck, bootstrap/axiom0/src/driver/cmd_check.c, tests/driver]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/driver/pipeline.c]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-00-bootstrap.md, spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md, spec/decisions/ADR-0016-vs0-gate-fix-tasks.md]
covers: [REQ-TYP-124]
started: 2026-10-07 08:37:12
finished: 2026-10-07 09:04:06
---
# T115 — VS0 fix: typeck diagnostics, literal range, float rejection, main signature in check

## Goal
`axiom0 check` reports exactly the type errors SPEC-03 prescribes for the bootstrap subset, once
each, so the VS0 gate (T022) no longer fails in typeck/driver. Fix task created by the T022 unblock
(ADR-0016); bugs T1–T5 of `_workspaces/reports/T022-report.md`.

## Scope
- T1: one type error emits `AX_TYPE_MISMATCH` exactly once (dedupe at the coercion seam: the error
  is reported where the mismatch is detected, not again at the enclosing coercion site).
- T2: AXS-SEM-021 literal range check — an integer literal (including a negated literal) outside
  its target type is a compile error; negating an unsigned literal is an error; literals above u64
  stay the lexer's `AX_LEX_INT_OVERFLOW` (AXS-LEX-054).
- T3: float types/literals are rejected with the AXS-SEM-010 diagnostic (floats are not in axiom0).
- T4: the `main` signature (AX_TYPE_MAIN_SIGNATURE) is checked in `check`, not only in `stage_run`
  (`pipeline.c` ~191–206); only AX_TYPE_MAIN_MISSING stays build/run-only (TYPE.def).
- T5: remove the hard-coded `strstr(main_file, "tests/driver/test.ax")` branch in
  `pipeline.c:196`; adjust `tests/driver` so the behaviour it tested is triggered by a real
  condition (or the test is removed with a reason in the report).
- Seam: typeck gets an exhaustive default for expression kinds — an unknown HIR kind is an ICE
  (or a diagnostic), never silently typed.
- One ui test per bug under `tests/ui/typeck/`.

## Acceptance
- [ ] New `tests/ui/typeck` tests for T1–T4 pass; `tests/driver` passes without the hard-coded path.
- [ ] In a snapshot with T022's suite present, these vs0 tests pass in check mode:
      sem_t16_no_implicit_widening, seam_duplicate_diag_once, call_arg_type_mismatch,
      lit_bool_not_integer, lit_mixed_signedness, sem_t15_literal_out_of_range, lit_minus_129_i8,
      lit_neg_unsigned, float_unsupported, main_with_params, main_returns_i64.
- [ ] `grep -n "tests/" bootstrap/axiom0/src/driver/*.c` finds no test path in production code.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T115-report.md` with exact `## Files changed`.

## Out of scope
- Parser (T114), MIR builder (T116), interpreter (T117). Do not edit `tests/conformance/vs0`.
- Casts, intrinsics and other MS-P5 features.

## Notes
- T017 (typeck) and T016 (driver) delivered the code; both are done, so this is a fix task, not a
  reopen. `pipeline.c` is shared: hold it only through `locks:`.

## Log
- 2026-10-06 23:44:39 started (attempt 1) T115-impl
- 2026-10-07 07:50:23 requeue: quota 429 (infrastructure failure: attempt refunded)
- 2026-10-07 08:37:12 started (attempt 1) T115-impl
- 2026-10-07 09:04:06 accepted by QA -> done
