---
id: T015
title: HIR data model + AST→HIR lowering
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T014]
priority: 25
status: done
attempts: 1
paths: [bootstrap/axiom0/src/hir, tests/hir, bootstrap/axiom0/src/driver/emit_hir.c]
locks: [bootstrap/axiom0/src/diag/codes/NAME.def]
spec: [0156, 0023, tasks/0378, 0159]
started: 2026-10-05 22:05:27
finished: 2026-10-05 22:27:20
---
# T015 — HIR data model + AST→HIR lowering

## Goal
Produce the semantic HIR consumed by typeck: resolved IDs, desugared syntax, spans preserved.

## Scope
- HIR data model with node kinds for the whole grammar (reserved up front, 0263 §42); lowering implemented for everything T011 parses. Constructs parsed only by T012 are lowered by T015b — until then they produce a "not supported yet" diagnostic, never a crash. Desugar compound assignment, else-if chains, `for` placeholders (full desugar in T072), method-call node kept explicit.
- `inspect --emit=hir` stable dump.

## Acceptance
- [ ] Golden tests covering every AST node kind T011 produces; `tests/hir/COVERAGE.md` maps AST kind → test file (QA cross-checks it against the AST enum).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T015-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-05 22:05:27 started (attempt 1) T015-impl
- 2026-10-05 22:27:20 accepted by QA -> done
