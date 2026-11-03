---
id: T652
title: E16.9 — Linux x86-64 static ELF64, SysV ABI & WSL execution conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T651]
priority: 95
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_9_linux_x64_static]
spec: [spec/SPEC-80-linux-x86-64-elf-static.md, 0053, 0192, 0255, 0256]
covers: [REQ-TGT-102, REQ-TGT-105, REQ-TGT-106, REQ-TGT-111, REQ-TGT-112]
---
# T652 — E16.9 — Linux x86-64 static ELF64, SysV ABI & WSL execution conformance suite

## Goal
Certify the E16.9 exit criterion (`ROADMAP.md` §3): static Linux x86-64 ELF64 object and executable generation, System V AMD64 ABI calling convention compliance, and full run-suite parity under WSL / Linux.

## Scope
- Create `tests/conformance/p16/e16_9_linux_x64_static` covering:
  - System V AMD64 ABI stress cases: 1..10 integer/pointer arguments across `RDI, RSI, RDX, RCX, R8, R9` + stack spill, 1..10 float/vector arguments across `XMM0..XMM7` + stack spill, 8-byte and 16-byte struct classification (`INTEGER`, `SSE`, mixed `INTEGER+SSE`, `MEMORY` / `sret` in `RDI`), callee-saved register preservation (`RBX, RBP, R12..R15`), 16-byte `RSP` alignment before `call`, and red-zone leaf functions vs non-leaf functions.
  - ELF64 `ET_REL` and `ET_EXEC` structural verification (`e_machine == EM_X86_64`, `PT_LOAD` RX/R/RW segment permissions and 4 KiB alignment, symbol and `.rela.*` tables, `SHN_ABS` fixed-address symbols, byte-for-byte determinism across repeated builds).
  - Differential `--interp` vs `--target x86_64-linux` native execution under WSL / Linux (`Xin chào thế giới` UTF-8 stdout, CLI args, environment variables, file I/O, heap allocation, and panic exit code `101`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_9_linux_x64_static` pass (`--interp` and `--target x86_64-linux`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T652-report.md` with exact `## Files changed`.

## Out of scope
- Dynamic ELF (`PIE`, `.so`), tested in `T660`.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin chào thế giới` for greeting strings.

## Log
- 2026-11-03 08:35:00 created by T216 (P16 phase planning)
