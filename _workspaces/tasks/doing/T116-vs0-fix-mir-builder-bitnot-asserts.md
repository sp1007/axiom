---
id: T116
title: VS0 fix: MIR builder bit-not, checked-arithmetic asserts, exhaustive lowering
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T021]
priority: 11
status: doing
attempts: 1
paths: [bootstrap/axiom0/src/mir/build, tests/mir/build]
locks: [bootstrap/axiom0/src/interp/interp.c]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-00-bootstrap.md, spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md, spec/decisions/ADR-0016-vs0-gate-fix-tasks.md]
covers: [REQ-EXP-021]
started: 2026-10-07 08:37:13
agent: T116-impl
---
# T116 — VS0 fix: MIR builder bit-not, checked-arithmetic asserts, exhaustive lowering

## Goal
The THIR→MIR builder emits the MIR SPEC-03 / FP-03 prescribes — correct operators and explicit
`Assert` terminators for every trapping operation — so the oracle and later the native backend
(T023, AXS-BOOT-007) see the checks in MIR. Fix task created by the T022 unblock (ADR-0016); bugs
M1–M3 of `_workspaces/reports/T022-report.md`.

## Scope
- M1 `builder.c` ~238: unary `~` lowers to bitwise NOT, not NEG.
- M2: checked `+ - *`, unary `-`, `/` and `%` (zero divisor, MIN / -1) and shifts (amount out of
  range) lower to a checked operation plus `AX_MIR_TERM_ASSERT` with an edge to the panic path,
  using the SPEC-03 panic messages (AXS-SEM-071). The data model, printer, text parser and verifier
  already support the terminator.
- M3: `build_expr_into` gets an exhaustive final branch — an unhandled HIR/THIR kind is an ICE
  (internal-error diagnostic), never silently dropped.
- Minimal interpreter support (lock on `interp/interp.c`): execute `AX_MIR_TERM_ASSERT`
  (continue on success, take the existing panic path on failure) so the full suite stays green.
  Nothing else in the interpreter — width/bitwise/panic-format work is T117.
- Regenerate `tests/mir/build/first_mir.mir` (FP-03 with the checked Add + assert edge) and add
  MIR goldens for `~`, division and shift asserts; the verifier accepts every new golden.

## Acceptance
- [ ] `tests/mir/build` goldens (regenerated FP-03 + new ones) pass and verify.
- [ ] In a snapshot with T022's suite present, `seam_bitnot_value` no longer fails in MIR.
- [ ] An ICE test (or C unit test) shows an unhandled kind is reported, not dropped.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T116-report.md` with exact `## Files changed`.

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
