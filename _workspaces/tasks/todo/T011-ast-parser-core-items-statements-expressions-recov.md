---
id: T011
title: AST + parser core (items, statements, expressions, recovery)
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T010]
priority: 21
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/syntax, tests/parse, tests/ui/parse, bootstrap/axiom0/src/driver/emit_ast.c]
locks: [bootstrap/axiom0/src/diag/codes/PARSE.def]
spec: [spec/SPEC-02-grammar.md, 0155, 0174, tasks/0386, tasks/0476]
started: 2026-10-05 16:36:55
unblocks: 1
---
# T011 — AST + parser core (items, statements, expressions, recovery)

## Goal
Parse the core grammar into an arena AST with spans and robust error recovery.

## Scope
- AST data model for the whole v0.1 grammar (so later parser work only adds parsing).
- Parse: fn, struct, enum, type alias, const, static, use (groups, alias), module decl; let/let mut/assignment/compound/expr statements/return/break/continue; blocks; if/else-if/else, match, loop, while, for; Pratt expressions with SPEC-02 precedence, calls, field/tuple/index access, DottedChain, struct literals, arrays, tuples, ranges, `?`, unary ops, casts `as`.
- Newline termination + continuation rules; optional `;`.
- Recovery: sync at newline/`}`/`)`/`]`/EOF; error nodes; no cascades of more than 1 diagnostic per construct.
- `inspect --emit=ast` stable S-expression-like dump.
- Parsed here because the first vertical slice needs them (ADR-0005 §4): simple types — named paths without generic arguments, unit, tuple types, `[N]T`; basic patterns — binding, `mut` binding, wildcard, literal, tuple. Everything else in types and patterns is T012.
- The AST dump is the emitter file `src/driver/emit_ast.c` (T004 table).

## Acceptance
- [ ] Golden tests: every construct + all example programs of SPEC-02.
- [ ] ui tests (under tests/ui/parse): missing `)`, missing expression, `var x = 1` (AX_PARSE_VAR fix-it), `import a` fix-it, stray tokens; parser never crashes on the fuzz-lite loop in the report.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T011-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-05 16:36:55 started (attempt 1) T011-impl
- 2026-10-05 19:37:38 block: Lexer offset regression from T010 requires fixing tests/lex which is outside T011 paths
- 2026-10-05 20:13:26 unblocked (cycle 1) 
