---
id: T060
title: Modules & packages: multi-file, visibility, use, re-exports, prelude module
phase: P7-abstraction
owner: axiom-frontend
reviewer: axiom-qa
depends: [T052]
priority: 80
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/resolve, bootstrap/axiom0/src/source, bootstrap/axiom0/src/driver, tests/modules, tests/ui/modules]
spec: [0103, 0108, tasks/0357, tasks/0306, 0141, 0168, 0047]
---
# T060 — Modules & packages: multi-file, visibility, use, re-exports, prelude module

## Goal
Real module system with dotted paths.

## Scope
- `module a.b` declarations and file→module mapping, package root and minimal manifest per spec 0168 (decide name/format with architect if unclear), `use` groups/aliases/re-exports, visibility pub/pub(package)/pub(module)/private enforcement, cycles handling, prelude as a real std module.

## Acceptance
- [ ] Multi-file test projects under tests/modules; ui tests for privacy and unresolved imports.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T060-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
