---
id: T012
title: Parser: types, patterns, generics, traits/impls, attributes, closures
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T011]
priority: 22
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/syntax, tests/parse]
spec: [spec/SPEC-02-grammar.md, tasks/0476, 0065, 0066]
---
# T012 — Parser: types, patterns, generics, traits/impls, attributes, closures

## Goal
Complete the grammar: everything not covered by T011.

## Scope
- Types: paths with generics, `[N]T`, `view<T>`, `mut_view<T>`, `*const T`/`*mut T`, fn types, tuples, `dyn Trait`, `Self`.
- Patterns: literal, binding (mut), wildcard, tuple, struct, variant (dotted), range, or-patterns if in spec.
- Generic params with bounds, where clauses; trait decls (methods, default bodies, assoc type/const, supertraits); impl blocks (`impl Trait for T`, inherent if spec'd); attributes `@name(args)`; visibility forms; closures; unsafe blocks; generic-argument commit rule in expressions (`Vec<i32>.new()`, `size_of<T>()`).

## Acceptance
- [ ] Golden tests per construct; ambiguity tests for `a < b` vs `f<T>(x)`; ui tests for malformed generics/patterns.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T012-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
