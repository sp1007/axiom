---
id: T058
title: E14.4 dyn Trait: vtables and dynamic dispatch
phase: P14-comptime-2-0-reflection-gener
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T214]
priority: 78
status: todo
attempts: 0
paths: [compiler/traits/dyn, compiler/mir, compiler/interp, tests/run/dyn, tests/ui/dyn]
spec: [tasks/0476, 0212]
---
# T058 — dyn Trait: vtables and dynamic dispatch

## Goal
Explicit dynamic dispatch.

## Scope
- dyn compatibility rules, coercion to dyn, vtable layout (spec'd), dispatch in interp.

## Acceptance
- [ ] run + ui tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T058-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- `paths` are provisional: T076 fixes the `compiler/<module>` layout and re-paths this task (ADR-0005 §8).
- Roadmap epic E14.4 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; the phase planning task may split it, keeping this id for the first slice.
- Includes native vtable emission (previously in T059).
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
