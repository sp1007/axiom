---
id: T422a
title: Fix — parser reads `a.f < b.g` as generic arguments (FU-A); a generic function `g<F>` cannot be used as a value (FU-J)
phase: P11-concurrency-async
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T434]
priority: 24
status: todo
attempts: 0
timeout_min: 600
paths: [tests/parse/generic_args_ambiguity, tests/run/generic_fn_value]
locks: [compiler/syntax, compiler/parser, compiler/types/typeck.ax, compiler/mir/builder.ax, spec/SPEC-02-grammar.md, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-02-grammar.md]
covers: [REQ-TST-072, REQ-TST-062]
---
# T422a — Fix: `<` after a field access, and generic functions as values

## Goal
`if other.deadline_ns < self.deadline_ns {` parses as a comparison, and `let f: fn(..) -> u32 = g<F>;` (explicit
instantiation of a generic function used as a function-pointer value) parses, type-checks and runs (T422 FU-A, FU-J;
ADR-0042 §2).

## Scope
- FU-A repro: `if other.deadline_ns < self.deadline_ns {` -> `AX_PARSE_EXPECTED_TOKEN: Expected '>'`. Apply the
  disambiguation rule of SPEC-02 for `<` after an expression path/field (generic arguments in expression position need
  the form SPEC-02 defines; a field access followed by `<` is a comparison). If SPEC-02 leaves the case open, implement
  "field access never takes generic arguments" and report it under "Spec deviations" (the architect amends SPEC-02).
- FU-J repro: `let f: fn(..) = g<F>;` gives `AX_PARSE_CHAINED_COMPARISON`. An item path with explicit generic arguments
  in value position is an instantiated function value (SPEC-02 rule for generic args in expressions); typeck and MIR
  lower it to the instantiated symbol (natively too).
- Tests: `tests/parse/generic_args_ambiguity/*` (goldens: comparison vs generic call, chained comparison still
  diagnosed), `tests/run/generic_fn_value/*.ax` (interp/native/native-O1, exact `// stdout:`).
- Regenerate selfhost bundles of edited modules with their generators.

## Acceptance
- [ ] Both repros compile and run; `a < b > c` still reports `AX_PARSE_CHAINED_COMPARISON`.
- [ ] `tests/parse`, `tests/lex` results unchanged except the new tests (baseline ids excepted).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new tests.
- [ ] Report `_workspaces/reports/T422a-report.md` with exact `## Files changed`.

## Out of scope
- Editing SPEC-02 (architect does it from the report), `std/`, `bootstrap/axiom0`, `docs/`.

## Notes
- Depends on T434 (owner of `compiler/syntax` / `compiler/parser` for the dump-leak fix).
- `spec/SPEC-02-grammar.md` is in `locks:` only so no spec task edits it concurrently; the engineer does not edit it.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T422 FU-A, FU-J)
