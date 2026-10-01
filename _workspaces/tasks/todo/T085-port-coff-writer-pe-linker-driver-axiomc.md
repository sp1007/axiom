---
id: T085
title: Port COFF writer, PE linker, driver → axiomc
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T084]
priority: 119
status: todo
attempts: 0
paths: [compiler/obj_link_driver, tests/selfhost/obj_link_driver]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
---
# T085 — Port COFF writer, PE linker, driver → axiomc

## Goal
Port COFF writer, PE linker, driver → axiomc, keeping behaviour identical to the C implementation.

## Scope
- Idiomatic canonical Axiom port of the corresponding axiom0 modules; same data model and diagnostics codes.
- Differential test harness comparing outputs with axiom0 over the whole tests/ corpus.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T085-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Template task: T076 splits it per C module (≤ ~1.5k lines of Axiom per task), names the exact differential artefact and harness entry, and may change these `paths` (ADR-0005 §8). This id stays as the group's integration + differential task.
- Module tests run in both modes: OS and heap access go through std (host intrinsics, ADR-0002); maps iterate in insertion order and hash like axiom0 (ADR-0004 §4), so dumps are byte-identical.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
