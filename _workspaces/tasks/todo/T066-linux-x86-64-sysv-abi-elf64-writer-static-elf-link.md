---
id: T066
title: E16.9 Linux x86-64: SysV ABI, ELF64 writer, static ELF linker
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T216]
priority: 93
status: todo
attempts: 0
paths: [compiler/abi/sysv, compiler/obj/elf, compiler/link/elf, tests/run/linux]
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
- `paths` are provisional: T076 fixes the `compiler/<module>` layout and re-paths this task (ADR-0005 §8).
- Roadmap epic E16.9 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; the phase planning task may split it, keeping this id for the first slice.
- 
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
