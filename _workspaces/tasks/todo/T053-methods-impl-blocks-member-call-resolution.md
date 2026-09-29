---
id: T053
title: Methods, impl blocks, member-call resolution
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
depends: [T052]
priority: 73
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/traits, tests/run/method, tests/ui/method]
spec: [0112, tasks/0476, tasks/0614]
---
# T053 — Methods, impl blocks, member-call resolution

## Goal
Method call syntax and resolution order.

## Scope
- `fn f(self: view<T>)` methods, receivers by value/view/mut_view with automatic ephemeral capability, member call resolution order (inherent → trait → imported extension → generic extension), UFCS `T.f(x)`.

## Acceptance
- [ ] run + ui tests for each resolution rule and ambiguity.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T053-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
