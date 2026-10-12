---
id: T053
title: Methods, impl blocks, member-call resolution
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T052]
priority: 73
status: doing
attempts: 0
paths: [bootstrap/axiom0/src, tests/run/method, tests/ui/method]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/diag/codes/TRAIT.def]
spec: [0112, tasks/0476, tasks/0614]
---
# T053 — Methods, impl blocks, member-call resolution

## Goal
Method call syntax and resolution order.

## Scope
- `fn f(self: view<T>)` methods, receivers by value/view/mut_view with automatic ephemeral capability, inherent member call resolution, UFCS `T.f(x)` for inherent methods (trait and extension methods deferred to T055).
- View receivers (moved from T048, ADR-0006 §6): `self: view<T>` / `mut_view<T>` with the automatic ephemeral capability at the call, checked by the T048 analysis.
- Inherent impls on built-in types when declared in std (needed by T069: `u32.min`, `char.len_utf8`, …) per the spec's rule for who may add them.

## Acceptance
- [ ] run + ui tests for each resolution rule and ambiguity. Run tests carry `// native-after: T059` (removed by T059).
- [ ] At least one positive run test and one negative ui test per Scope bullet; the report maps each bullet to its test files (QA checks the map).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T053-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
