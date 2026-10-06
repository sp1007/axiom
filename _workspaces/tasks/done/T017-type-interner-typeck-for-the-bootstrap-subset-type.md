---
id: T017
title: Type interner + typeck for the bootstrap subset (typed HIR)
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T015, T016, T003, T003a, T111]
priority: 30
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types, tests/typeck, tests/ui/typeck, bootstrap/axiom0/src/driver/emit_thir.c, bootstrap/axiom0/src/driver/driver.h, bootstrap/axiom0/src/driver/cmd_check.c]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/driver/pipeline.c]
timeout_min: 300
spec: [0157, 0175, 0245, tasks/0388, tasks/0482, spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md]
started: 2026-10-06 09:15:15
unblocks: 1
finished: 2026-10-06 09:26:25
---
# T017 — Type interner + typeck for the bootstrap subset (typed HIR)

## Goal
Type the subset: integers (all widths), bool, unit, never, functions, let (annotated/inferred), literals, operators, if/while/loop/return, calls.

## Scope
- TypeInterner (hash-consed TypeId), primitive types, function types.
- Local inference with literal defaulting per SPEC-03; no implicit conversions; operator typing table.
- Typed HIR (THIR) with a type on every expression; `inspect --emit=thir`.
- Diagnostics: AX_TYPE_MISMATCH, AX_TYPE_UNKNOWN, AX_TYPE_NOT_CALLABLE, AX_TYPE_ARG_COUNT, AX_TYPE_RETURN…

## Acceptance
- [ ] First negative test `return true` in i32 fn → AX_TYPE_MISMATCH.
- [ ] ui tests for each rule; golden THIR tests; i32→i64 assignment rejected.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T017-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Depends on T111 (ADR-0005 §6): the requirement backlog is complete before the semantic core starts. Depends on T016 for `check` (ui tests) and the pipeline.
- Scope boundary with T030–T032: this task types immutable `let`, literals, operators, `if`/`while`/`loop` as statements, direct calls and `return`. Mutation, value-producing control flow and the remaining function forms are T030–T032.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 07:08:03 started (attempt 1) T017-impl
- 2026-10-06 09:14:18 block: needs bootstrap/axiom0/src/driver/driver.h and cmd_check.c added to paths
- 2026-10-06 09:14:57 unblocked (cycle 1) 
- 2026-10-06 09:15:15 started (attempt 1) T017-impl
- 2026-10-06 09:26:25 accepted by QA -> done
