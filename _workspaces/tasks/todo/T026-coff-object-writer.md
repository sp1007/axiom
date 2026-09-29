---
id: T026
title: COFF object writer
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
depends: [T024, T003a]
priority: 43
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/obj/coff, tests/obj]
spec: [0185, .claude/skills/axiom-x64-backend/references/pe-coff.md, spec/SPEC-04-core-extensibility.md]
---
# T026 — COFF object writer

## Goal
Write deterministic COFF (.obj) files from the object model.

## Scope
- Headers, sections, symbols (long names via string table), relocations REL32/ADDR64/ADDR32NB, TimeDateStamp 0.
- `axiom0 build --emit=obj`.

## Acceptance
- [ ] objdump -x/-d accepts outputs and shows expected symbols/relocations; byte-identical across two runs.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T026-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
