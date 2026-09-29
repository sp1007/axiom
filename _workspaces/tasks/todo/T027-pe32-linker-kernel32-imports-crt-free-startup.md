---
id: T027
title: PE32+ linker + kernel32 imports + CRT-free startup
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
depends: [T026]
priority: 44
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/link/pe, bootstrap/axiom0/src/link/startup, tests/link]
spec: [0186, 0187, 0164, 0217, .claude/skills/axiom-x64-backend/references/pe-coff.md]
---
# T027 — PE32+ linker + kernel32 imports + CRT-free startup

## Goal
Link our COFF objects into a runnable PE32+ console executable without any external tool or CRT.

## Scope
- Read our COFF, merge sections, resolve symbols, apply relocations, lay out image, import directory + IAT for KERNEL32.dll!ExitProcess, startup `axiom_start` (sub rsp,40; call main; mov ecx,eax; call [ExitProcess]).
- Deterministic output; undefined/duplicate symbol diagnostics (AX_LINK_*).

## Acceptance
- [ ] A hand-built object (test fixture) with `main` returning 42 links and runs → exit code 42.
- [ ] objdump -x shows correct headers/imports; byte-identical rebuild.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T027-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
