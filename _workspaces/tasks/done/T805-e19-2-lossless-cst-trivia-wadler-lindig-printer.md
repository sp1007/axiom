---
id: T805
title: E19.2 Lossless CST trivia attachment, Wadler-Lindig layout engine & canonical AST printer
phase: P19-developer-tooling
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T804]
priority: 195
status: done
attempts: 1
paths: [compiler/fmt/cst, compiler/fmt/printer, tests/run/fmt_engine]
spec: [spec/SPEC-101-canonical-formatter.md, spec/SPEC-01-lexical.md, spec/SPEC-02-grammar.md, tasks/0476, tasks/0693, tasks/0695]
covers: [REQ-TOOL-183, REQ-TOOL-298]
started: 2026-11-08 13:29:57
finished: 2026-11-08 16:22:36
---
# T805 — E19.2 Lossless CST trivia attachment, Wadler-Lindig layout engine & canonical AST printer

## Goal
Implement lossless CST trivia attachment, the Wadler-Lindig pretty-printing layout engine, and the canonical Axiom syntax printer in `compiler/fmt/cst` and `compiler/fmt/printer` per `spec/SPEC-101-canonical-formatter.md`.

## Scope
- Implement lossless trivia attachment in `compiler/fmt/cst` over the shared compiler lexer/parser (`REQ-TOOL-183`, `REQ-TOOL-298`) capturing leading, trailing, and dangling comments (`//`, `/* */`, `///`, `//!`) and blank-line separators (`tasks/0476 §217.97-99`).
- Implement the deterministic Wadler-Lindig `Doc` combinator engine (`Group`, `Indent`, `Line`, `SoftLine`, `IfBreak`, `LineSuffix`) and canonical Axiom node printer in `compiler/fmt/printer` covering items (`module`, `use`, `fn`, `struct`, `enum`, `union`, `trait`, `impl`, `const`, `static`), generics/where-clauses, `match` arms, chained `.` calls, closures, and attributes (`@at`, `@repr`, `@cfg`).

## Acceptance
- [ ] Run tests in `tests/run/fmt_engine` verify canonical formatting, comment preservation across line breaks, and single-pass idempotence (`fmt(fmt(x)) == fmt(x)`) across all Axiom declaration, expression, and pattern constructs.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T805-report.md` with exact `## Files changed`.

## Out of scope
- CLI driver subcommand `axiomc fmt` and LSP formatting handler (`T806`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T805/build` and `python tools/axtest.py --compiler build-snap-T805/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 13:29:57 started (attempt 1) T805-impl
- 2026-11-08 16:22:36 accepted by QA -> done
