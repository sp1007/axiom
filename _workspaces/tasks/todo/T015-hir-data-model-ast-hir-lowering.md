---
id: T015
title: HIR data model + AST→HIR lowering
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
depends: [T014]
priority: 25
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/hir, tests/hir]
spec: [0156, 0023, tasks/0378, 0159]
---
# T015 — HIR data model + AST→HIR lowering

## Goal
Produce the semantic HIR consumed by typeck: resolved IDs, desugared syntax, spans preserved.

## Scope
- HIR nodes for all items/exprs/stmts/patterns/types; desugar compound assignment, else-if chains, `for` placeholders (full desugar in T072), method-call node kept explicit.
- `inspect --emit=hir` stable dump.

## Acceptance
- [ ] Golden tests covering every AST node kind (QA will cross-check exhaustiveness).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T015-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
