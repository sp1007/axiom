---
id: T079b
title: Port recursive-descent parser to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T079a]
priority: 113
status: done
attempts: 1
paths: [compiler/syntax/parse.ax, compiler/syntax/parse, tests/selfhost/parse]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-022]
started: 2026-10-14 15:12:56
finished: 2026-10-14 20:24:23
---
# T079b — Port recursive-descent parser to Axiom

## Goal
Port the recursive-descent parser and Pratt expression parser (`compiler/syntax/parse.ax`) from C to Axiom.

## Scope
- Port top-level item parser, statement parser, type parser, pattern parser, and Pratt expression parser.
- Match grammar specification from `spec/SPEC-02-grammar.md` and error recovery from `bootstrap/axiom0/src/syntax/parse.c`.
- Unit tests under `tests/selfhost/parse/`.

## Acceptance
- [ ] Parser implemented in `compiler/syntax/parse.ax` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Parsed AST matches `axiom0 inspect --emit=ast` on representative syntax tests.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T079b-report.md` with exact `## Files changed`.

## Out of scope
- Full corpus differential validation (handled in integration task T079).

## Notes
- Sub-task of T079 split per ADR-0005 §8 and SPEC-20 §4.3.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 12:45:40 started (attempt 1) axiom-frontend
- 2026-10-14 15:12:45 requeue: session restart; continue from files (not charged: attempt refunded)
- 2026-10-14 15:12:56 started (attempt 1) T079b-impl
- 2026-10-14 20:24:23 accepted by QA -> done
