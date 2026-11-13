---
id: T483
title: Register AX_CONST_SHIFT_RANGE for compile-time out-of-range shifts; fold unary minus into integer literals (i64.MIN)
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T452]
priority: 27
status: todo
attempts: 0
timeout_min: 600
paths: [tests/ui/const_shift_range, tests/run/int_min_literals]
locks: [compiler/diag/code.ax, compiler/diag/explain/mod.ax, compiler/interp, compiler/interp_opt/session.ax, compiler/types/typeck.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-40-integers.md, spec/SPEC-03-core-semantics.md, spec/diagnostics.md]
covers: [REQ-TST-025, REQ-TST-096]
---
# T483 — `AX_CONST_SHIFT_RANGE` and MIN literals

## Goal
Compile-time evaluation reports `AX_CONST_SHIFT_RANGE` for a shift count `< 0` or `>= T.BITS` (SPEC-40 AXS-INT-005,
SPEC-03 AXS-SEM-037 as amended by ADR-0042 §4), and `-9223372036854775808i64` (every `T.MIN` literal) is a valid
literal (SPEC-40 AXS-INT-004: range check after folding unary `-`).

## Scope
- Register `AX_CONST_SHIFT_RANGE` in `compiler/diag/code.ax` (next free compiler id; name table; `explain` entry in
  `compiler/diag/explain/mod.ax`; `spec/diagnostics.md` is updated by the architect from the report).
- Constant evaluation (`compiler/interp` const path and `compiler/interp_opt/session.ax`) emits it instead of
  `AX_CONST_OVERFLOW` for shifts, all widths incl. 128-bit; runtime shifts keep panicking `shift amount out of range`.
- Observed (T452-qa): `-9223372036854775808i64` panics `arithmetic overflow` at run time (old and new compiler). Fold
  unary `-` applied directly to an integer literal before the range check (typeck), for `i8..i128`/`isize`; a literal
  `9223372036854775808i64` without `-` still reports `AX_TYPE_LITERAL_OUT_OF_RANGE`.
- Tests: `tests/ui/const_shift_range/*` (`const X: u128 = 1u128 << 128u128;`, negative count, `u8 << 8`, i128),
  `tests/run/int_min_literals/*.ax` (every signed MIN literal printed; interp/native/native-O1, exact `// stdout:`).
- Regenerate selfhost bundles of edited modules with their generators.

## Acceptance
- [ ] UI tests report exactly `AX_CONST_SHIFT_RANGE` with the shift span; overflow cases still `AX_CONST_OVERFLOW`.
- [ ] MIN literal tests pass in all modes; the out-of-range literal test still fails with its code.
- [ ] `tests/opt/int128`, `tests/run/int128_interp`, `tests/run/comptime` pass.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new run tests.
- [ ] Report `_workspaces/reports/T483-report.md` with exact `## Files changed` and the assigned numeric id.

## Out of scope
- `spec/` edits, `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §4; T452-qa spec gap and i64 MIN literal)
