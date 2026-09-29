---
id: T066
title: Linux x86-64: SysV ABI, ELF64 writer, static ELF linker
phase: P8-backend
owner: axiom-backend
reviewer: axiom-qa
depends: [T063]
priority: 93
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/abi/sysv, bootstrap/axiom0/src/obj/elf, bootstrap/axiom0/src/link/elf, tests/run/linux]
spec: [0192, 0053, 0255, 0256]
---
# T066 — Linux x86-64: SysV ABI, ELF64 writer, static ELF linker

## Goal
Second target: static Linux executables testable through WSL.

## Scope
- SysV ABI description, ELF64 relocatable writer, static linker (ET_EXEC), `_start` → main → exit syscall, `--target x86_64-linux`; runner executes via `wsl` when available (skip otherwise).

## Acceptance
- [ ] All run tests pass for x86_64-linux under WSL.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T066-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
