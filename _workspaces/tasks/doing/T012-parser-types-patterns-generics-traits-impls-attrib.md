---
id: T012
title: Parser: types, patterns, generics, traits/impls, attributes, closures
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T011]
priority: 23
status: doing
attempts: 1
paths: [bootstrap/axiom0/src/syntax, tests/parse, tests/ui/parse, tests/resolve/]
locks: [bootstrap/axiom0/src/diag/codes/PARSE.def]
spec: [spec/SPEC-02-grammar.md, tasks/0476, 0065, 0066]
started: 2026-10-05 22:08:36
unblocks: 1
agent: T012-impl
---
# T012 — Parser: types, patterns, generics, traits/impls, attributes, closures

## Goal
Complete the grammar: everything not covered by T011.

## Scope
- Types: paths with generics, `[N]T`, `view<T>`, `mut_view<T>`, `*const T`/`*mut T`, fn types, tuples, `dyn Trait`, `Self`.
- Patterns: literal, binding (mut), wildcard, tuple, struct, variant (dotted), ranges (`'a'..='z'`, integer ranges), or-patterns (ADR-0004 §7).
- Generic params with bounds, where clauses; trait decls (methods, default bodies, assoc type/const, supertraits); impl blocks (`impl Trait for T`, inherent if spec'd); attributes `@name(args)`; visibility forms; closures; unsafe blocks; generic-argument commit rule in expressions (`Vec<i32>.new()`, `size_of<T>()`).
- Items: `extern "C"` / `extern "system"` blocks and items with attributes such as `@link("kernel32")`, `unsafe fn` (consumed by T061a/T065); labelled loops and `break`/`continue` to a label; sub-range index forms `s[a..b]`, `s[a..]`, `s[..b]`; `const` items of aggregate type.
- Types and patterns already parsed by T011 are not redone. Name resolution and HIR lowering of the constructs parsed here are T015b.

## Acceptance
- [ ] Golden tests per construct; ambiguity tests for `a < b` vs `f<T>(x)`; ui tests for malformed generics/patterns.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T012-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-05 20:38:52 started (attempt 1) T012-impl
- 2026-10-05 21:53:56 block: need tests/resolve added to paths to update resolve tests (currently locked by T014)
- 2026-10-05 22:08:11 unblocked (cycle 1) 
- 2026-10-05 22:08:36 started (attempt 1) T012-impl
