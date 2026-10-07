---
id: T114
title: VS0 fix: parser expression precedence, associativity and control-flow headers
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T013, T015b]
priority: 11
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/syntax, tests/parse, tests/ui/parse, tests/hir, tests/resolve, tests/mir/build/control_flow.ax, tests/mir/build/control_flow.mir]
locks: [bootstrap/axiom0/src/diag/codes/PARSE.def]
spec: [spec/SPEC-02-grammar.md, spec/decisions/ADR-0010-grammar-forms-v0-1.md, spec/decisions/ADR-0016-vs0-gate-fix-tasks.md]
covers: [REQ-GRM-001, REQ-GRM-002]
started: 2026-10-07 08:37:12
unblocks: 1
---
# T114 — VS0 fix: parser expression precedence, associativity and control-flow headers

## Goal
The parser builds the expression tree SPEC-02 prescribes, so the VS0 gate (T022) no longer fails in
the parser. Fix task created by the T022 unblock (ADR-0016); bugs P1–P5 of
`_workspaces/reports/T022-report.md`.

## Scope
- P1 `parse.c` ~686/702/742/755: `if` / `while` / `match` / `for` headers parse a full expression
  (all binary operators), not only a primary — `if a == 3 {` must parse.
- P2 ~848/1013: binary operators are left-associative per the SPEC-02 precedence table
  (`10 - 3 - 2` is `(10 - 3) - 2`); comparison operators stay non-associative as SPEC-02 states.
- P3 ~527: prefix operators (`-`, `!`, `~`) bind tighter than every binary operator
  (`-1 + 8` is `(-1) + 8`).
- P4 ~559–569/608–617: the tentative generic-argument parse must not emit diagnostics before it
  backtracks (`n < 0 {`, `a < 2 < 3` give only the diagnostic the grammar prescribes).
- P5 ~577: in a control-flow header an `ident {` is not a struct literal (struct-literal
  restriction in headers, SPEC-02 / ADR-0010); parenthesised struct literals stay allowed.
- Update AST/HIR golden files whose tree changes because of the fix (each change explained in the
  report); add one parse golden per bug under `tests/parse/` pinning the corrected tree.
- Delete `tests/mir/build/control_flow.ax` and `tests/mir/build/control_flow.mir` as they are being deleted by parallel task T116 anyway (avoids needing a golden update).

## Acceptance
- [ ] New parse goldens for P1–P5 pass; changed goldens listed and justified in the report.
- [ ] In a snapshot with T022's suite present, these vs0 tests no longer fail in the parser:
      seam_if_cond_binary, seam_while_cond_binary, seam_sub_left_assoc, seam_div_left_assoc,
      seam_add_left_assoc_no_overflow, seam_unary_minus_binds_tight, cf_if_else_chain,
      cmp_non_associative, seam_if_header_ident_not_struct (they may still fail in later stages owned
      by T115/T116/T117 — state which stage in the report).
- [ ] Fuzz smoke (`tools/fuzz.py --smoke`) still passes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T114-report.md` with exact `## Files changed`.

## Out of scope
- Typeck, MIR, interpreter fixes (T115, T116, T117). Do not edit `tests/conformance/vs0` (T022 owns it).
- New syntax beyond SPEC-02.

## Notes
- Existing tests used `if (cond)` and masked P1; do not "fix" tests by adding parentheses.
- Canonical syntax only (axiom-syntax): `=` binding, `.` paths.

## Log
- 2026-10-06 23:44:39 started (attempt 1) T114-impl
- 2026-10-07 07:50:22 requeue: quota 429 (infrastructure failure: attempt refunded)
- 2026-10-07 08:37:12 started (attempt 1) T114-impl
- 2026-10-07 09:18:51 block: needs tests/mir in paths to fix tests/mir/build/control_flow.mir regression
- 2026-10-07 09:19:46 unblocked (cycle 1) 
