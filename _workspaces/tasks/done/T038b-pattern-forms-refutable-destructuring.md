---
id: T038b
title: Pattern forms: literal/range/or-patterns, guards, if-let, while-let, destructuring
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T038]
priority: 58
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/types/match, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, bootstrap/axiom0/src/hir, tests/run/pattern, tests/ui/pattern, tests/mir, tests/mc]
locks: [bootstrap/axiom0/src/diag/codes/PAT.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0065, tasks/0268, tasks/0392, tasks/0504]
covers: []
started: 2026-10-10 07:57:55
finished: 2026-10-10 09:12:21
---
# T038b — Pattern forms: literal/range/or-patterns, guards, if-let, while-let, destructuring

## Goal
Complete pattern matching for the self-host subset (split from T038, ADR-0005 §8): the forms a lexer and an instruction encoder written in Axiom need.

## Scope
- Literal patterns (integers, `char`, bool), range patterns (`'a'..='z'`, integer ranges), or-patterns, guards (per SPEC-02); exhaustiveness and unreachable-arm analysis extended to them (integer/char range coverage; a guarded arm never counts as covering).
- Refutable forms `if let`, `while let`, `let … else` desugared to `match`.
- Destructuring `let` for tuples and structs with an irrefutability check (AX_PAT_REFUTABLE).

## Acceptance
- [ ] Pattern tests with user-defined enums: `if let` / `while let`, destructuring `let (a, b) = pair` and struct patterns; a refutable pattern in a plain `let` is rejected.
- [ ] A lexer-style classifier `match c { 'a'..='z' | 'A'..='Z' | '_' => 1, '0'..='9' => 2, _ => 0 }` runs in interp; overlapping ranges give the unreachable-arm warning; a `u8` match covering 0..=255 by ranges needs no wildcard.
- [ ] Run tests carry `// native-after: T040` (removed by T040).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T038b-report.md` with exact `## Files changed`.

## Out of scope
- Option/Result (T039); slice patterns and binding-at patterns unless SPEC-02 puts them in the self-host subset.
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 07:57:55 started (attempt 1) 
- 2026-10-10 09:12:21 accepted by QA -> done
