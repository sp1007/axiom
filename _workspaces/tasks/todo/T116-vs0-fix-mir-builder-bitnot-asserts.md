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
status: todo
attempts: 1
paths: [bootstrap/axiom0/src/mir/build, tests/mir/build]
locks: [bootstrap/axiom0/src/interp/interp.c, bootstrap/axiom0/src/mir/mir.h, bootstrap/axiom0/src/mir/parse.c, bootstrap/axiom0/src/mir/print.c, bootstrap/axiom0/src/verify/verify.c]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-00-bootstrap.md, spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md, spec/decisions/ADR-0016-vs0-gate-fix-tasks.md, spec/decisions/ADR-0017-checked-arithmetic-mir.md]
covers: [REQ-EXP-021]
started: 2026-10-07 10:01:32
unblocks: 1
---
# T116 â€” VS0 fix: MIR builder bit-not, checked-arithmetic asserts, exhaustive lowering

## Goal
The THIRâ†’MIR builder emits the MIR SPEC-03 / FP-03 prescribes â€” correct operators and explicit
`Assert` terminators for every trapping operation â€” so the oracle and later the native backend
(T023, AXS-BOOT-007) see the checks in MIR. Fix task created by the T022 unblock (ADR-0016); bugs
M1â€“M3 of `_workspaces/reports/T022-report.md`.

## Scope
- M1 `builder.c` ~238: unary `~` lowers to bitwise NOT, not NEG.
- M2: Rename `AX_MIR_RVALUE_CHECKED_BINARY_OP` in `mir.h` to `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP` (returning bool, ADR-0017). Checked operations (`+ - *`, `/`, `%`, shifts, unary `-`) lower to computing the overflow bool (via explicit comparisons or `OverflowsBinaryOp`), an `AX_MIR_TERM_ASSERT` asserting it is false, and then the standard `BinaryOp`.
  Update the printer, text parser, verifier and interpreter to support `OverflowsBinaryOp` and the `Assert` terminator.
- M3: `build_expr_into` gets an exhaustive final branch â€” an unhandled HIR/THIR kind is an ICE
  (internal-error diagnostic), never silently dropped.
- Minimal interpreter support (lock on `interp/interp.c`): execute `AX_MIR_TERM_ASSERT`
  (continue on success, take the existing panic path on failure) so the full suite stays green.
  Nothing else in the interpreter â€” width/bitwise/panic-format work is T117.
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
- 2026-10-07 09:22:27 block: Missing CheckedBinaryOp in MIR, and no clear way to represent checked arithmetic without tuple support in the interpreter.
- 2026-10-07 09:25:56 unblocked (cycle 1) 
- 2026-10-07 10:01:32 started (attempt 1) T116-impl
- 2026-10-07 10:19:20 block: Interferes with T118
