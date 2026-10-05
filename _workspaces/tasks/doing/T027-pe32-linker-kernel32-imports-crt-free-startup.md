---
id: T027
title: PE32+ linker + kernel32 imports + CRT-free startup
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T026]
priority: 44
status: doing
attempts: 1
paths: [bootstrap/axiom0/src/link/pe, bootstrap/axiom0/src/link/startup, tests/link]
locks: [bootstrap/axiom0/src/diag/codes/LINK.def]
spec: [0186, 0187, 0164, 0217, .claude/skills/axiom-x64-backend/references/pe-coff.md]
started: 2026-10-05 21:54:07
agent: T027-impl
---
# T027 — PE32+ linker + kernel32 imports + CRT-free startup

## Goal
Link our COFF objects into a runnable PE32+ console executable without any external tool or CRT.

## Scope
- Read our COFF, merge sections, resolve symbols, apply relocations, lay out image, import directory + IAT for KERNEL32.dll!ExitProcess, startup `axiom_start` (sub rsp,40; call main; mov ecx,eax; call [ExitProcess]).
- Deterministic output; undefined/duplicate symbol diagnostics (AX_LINK_*).
- Linker option `--stack-reserve <bytes>` (SizeOfStackReserve, default 0x100000; commit stays 0x1000) — ADR-0003 C1; exposed on the command line by T028.
- Tests: C driver `tests/link/cdriver_pe.c` + `exec` manifests; fixtures under `tests/link/fixtures/`.

## Acceptance
- [ ] A hand-built object (test fixture) with `main` returning 42 links and runs → exit code 42.
- [ ] objdump -x shows correct headers/imports; byte-identical rebuild.
- [ ] A link with stack reserve 67108864 shows that value in the optional header (objdump -x); the default stays 0x100000.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T027-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-05 21:54:07 started (attempt 1) T027-impl
