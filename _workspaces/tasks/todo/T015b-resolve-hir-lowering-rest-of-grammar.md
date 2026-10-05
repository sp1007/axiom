---
id: T015b
title: Name resolution + HIR lowering for the rest of the grammar
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T012, T015]
priority: 27
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/resolve, bootstrap/axiom0/src/hir, tests/resolve, tests/hir, tests/ui/resolve, bootstrap/axiom0/src/driver/emit_resolved.c, bootstrap/axiom0/src/driver/emit_hir.c, bootstrap/axiom0/src/lex/lex.c]
locks: [bootstrap/axiom0/src/diag/codes/NAME.def]
spec: [0156, 0023, tasks/0378, tasks/0387, 0159, spec/SPEC-02-grammar.md]
covers: []
started: 2026-10-06 03:55:48
unblocks: 1
---
# T015b — Name resolution + HIR lowering for the rest of the grammar

## Goal
Finish the frontend for everything T012 parses, off the critical path of the first vertical slice (ADR-0005 §4): the semantic core T017–T021 starts after T015/T016 and does not wait for this task; the VS0 gate (T022) and P5 (T030) do.

## Scope
- Resolver: scopes and symbols for generic parameters and where clauses, trait declarations and their items, impl blocks (`Self`, associated items), closures (parameters, captured names stay ordinary uses), loop labels, all pattern forms (variant paths, struct patterns, ranges, or-patterns with consistent bindings), `extern` items, attributes.
- HIR lowering for the same constructs: types (`view<T>`, `mut_view<T>`, raw pointers, fn types, generic paths, `Self`), patterns, generics, traits/impls, closures, `unsafe` blocks and `unsafe fn`, `extern` items, labelled loops, sub-range index forms, attributes kept as data.
- `inspect --emit=resolved` and `--emit=hir` cover the new nodes (the emitter files of T014/T015 are in this task's `paths`).

## Acceptance
- [ ] Golden `resolved` and `hir` tests for every AST node kind T012 adds; `tests/hir/COVERAGE.md` now covers every AST kind (QA cross-checks against the AST enum: no kind without a test).
- [ ] ui tests: unknown generic parameter, duplicate binding in a pattern, inconsistent or-pattern bindings, unknown label, `Self` outside impl/trait.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T015b-report.md` with exact `## Files changed`.

## Out of scope
- Typing of these constructs (P5–P7 tasks); `dyn` beyond lowering to a HIR node that later reports "not supported in Stage-0" (E14.4).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- The AST and HIR data models already reserve every node kind (T011, T015): this task adds resolution and lowering code, not new data-model design.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 03:55:48 started (attempt 1) T015b-impl
- 2026-10-06 04:30:32 block: needs bootstrap/axiom0/src/lex/lex.c added to paths
- 2026-10-06 04:31:07 unblocked (cycle 1) 
