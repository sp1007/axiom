---
id: T035a
title: Structs syntax, lowering, resolution and typechecking
phase: P5-language
owner: axiom-frontend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T034]
priority: 55
status: doing
attempts: 2
paths: [bootstrap/axiom0/src/syntax, bootstrap/axiom0/src/hir, bootstrap/axiom0/src/resolve, bootstrap/axiom0/src/types, tests/ui/struct, bootstrap/axiom0/src/lir]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/driver/emit_ast.c, bootstrap/axiom0/src/driver/emit_hir.c, bootstrap/axiom0/src/driver/emit_thir.c, bootstrap/axiom0/src/driver/emit_resolved.c]
spec: [0059, 0081, 0043, tasks/0267, tasks/0281, 0009]
started: 2026-10-08 19:45:12
unblocks: 2
agent: T035a-impl
---
# T035a — Structs syntax, lowering, resolution and typechecking

## Goal
Implement parser, HIR lowering, name resolution, and typechecking for structs and tuples.

## Scope
- Struct decl/literal/field read/write syntax, nested structs, tuples + `.0`. Name resolution for struct names and field accesses. Typechecking and HIR lowering.

## Acceptance
- [ ] ui tests (unknown field, missing field, parser errors).
- [ ] Full test suite passes; build warning-free.
- [ ] Report `_workspaces/reports/T035a-report.md` with exact `## Files changed`.

## Notes
- First part of original T035.

## Log
- 2026-10-08 19:20:05 started (attempt 1) T035a-impl
- 2026-10-08 19:33:00 block: needs typeck.c, ast.h, hir.h, lower.c to properly implement and lower tuple expressions and pass type-checking ui tests for structs
- 2026-10-08 19:34:30 unblocked (cycle 1) 
- 2026-10-08 19:35:30 started (attempt 1) T035a-impl
- 2026-10-08 19:40:21 block: needs driver/emit_ast.c and emit_hir.c etc to handle new AX_EXPR_TUPLE variants due to Werror=switch
- 2026-10-08 19:41:04 unblocked (cycle 2) 
- 2026-10-08 19:42:17 started (attempt 1) T035a-impl
- 2026-10-08 19:44:38 block: needs driver/emit_thir.c and emit_resolved.c in locks to handle exhaustive switch for new tuple variants
- 2026-10-08 19:44:39 parked: unblock cap reached (unblocks=2, failed unblock agents=0); needs the owner
- 2026-10-08 19:45:12 started (attempt 2) T035a-impl

