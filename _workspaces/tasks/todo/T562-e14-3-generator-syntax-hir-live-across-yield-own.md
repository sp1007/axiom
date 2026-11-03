---
id: T562
title: E14.3 — Generator syntax (gen fn, yield), HIR lowering & live-across-yield capability/ownership analysis
phase: P14-comptime-2-0-reflection-genera
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T561]
priority: 182
status: todo
attempts: 0
paths: [compiler/syntax, compiler/hir, compiler/own, tests/ui/generators]
spec: [spec/SPEC-62-generators.md, tasks/0512, tasks/0539]
covers: [REQ-CORE-2999, REQ-CORE-3000, REQ-CORE-3001, REQ-CORE-3002, REQ-CORE-3003, REQ-CORE-3004, REQ-CORE-3005, REQ-CORE-3006, REQ-CORE-3007]
---
# T562 — E14.3 — Generator syntax (gen fn, yield), HIR lowering & live-across-yield capability/ownership analysis

## Goal
Implement lexer/parser/AST/HIR support for `gen fn` and `yield` expressions, type checking of yielded values, and live-across-`yield` ownership and capability verification per `spec/SPEC-62-generators.md`.

## Scope
- Extend `compiler/ast`, `compiler/parser`, and `compiler/hir` to parse and lower `gen fn` declarations and `yield <expr>` statements/expressions, rejecting `yield` outside a generator context (`AX_GEN_YIELD_OUTSIDE_GEN`).
- Compute per-`YieldPointId` live local sets and enforce capability/ownership rules across suspension points in `compiler/own`: reject self-referential borrows of generator locals across `yield` (`AX_GEN_SELF_BORROW_ACROSS_YIELD`), ephemeral capabilities crossing `yield` (`AX_GEN_VIEW_ACROSS_YIELD`), and unverified `Send`/`Share` derivation when suspended state holds non-`Send` locals (`AGEN-34..65`, `AMIR-29..37`).

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/generators` verify `gen fn` and `yield` parsing, `AX_GEN_YIELD_OUTSIDE_GEN`, `AX_GEN_SELF_BORROW_ACROSS_YIELD`, `AX_GEN_VIEW_ACROSS_YIELD`, and ownership tracking across multiple `yield` points.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T562-report.md` with exact `## Files changed`.

## Out of scope
- MIR state-machine transformation and per-state drop glue (`T563`) and `std.iter` combinators (`T564`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T562/build` and `python tools/axtest.py --compiler build-snap-T562/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:22:30 created by T214 (P14 phase planning)
