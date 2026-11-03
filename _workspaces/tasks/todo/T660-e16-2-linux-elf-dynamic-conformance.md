---
id: T660
title: E16.2 — Linux ELF PIE, GOT/PLT, shared object (.so) & libc interop conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T659]
priority: 103
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_2_linux_elf_dyn]
spec: [spec/SPEC-82-linux-elf-dynamic.md, 0197, tasks/0563]
covers: [REQ-TGT-305, REQ-TGT-306, REQ-TGT-309, REQ-TGT-310]
---
# T660 — E16.2 — Linux ELF PIE, GOT/PLT, shared object (.so) & libc interop conformance suite

## Goal
Certify the E16.2 exit criterion (`ROADMAP.md` §3): Linux ELF64 Position-Independent Executables (`PIE`), `GOT`/`PLT` dynamic relocations, shared objects (`.so`), symbol visibility, and bidirectional `libc` / C shared-library interoperability.

## Scope
- Create `tests/conformance/p16/e16_2_linux_elf_dyn` covering:
  - ELF64 `PIE` executable validation (`ET_DYN`, `PT_INTERP`, `PT_DYNAMIC`, `PT_GNU_RELRO`, `PT_GNU_STACK`, `DF_1_PIE`, ASLR base relocation via `R_X86_64_RELATIVE`).
  - Axiom-produced `.so` shared library (`--kind dll`) exporting `@export` functions and keeping non-exported functions `STV_HIDDEN`, linked and called by (a) an Axiom PIE executable, (b) `std.sys.linux_dl` (`dlopen`/`dlsym`), and (c) a `gcc`-compiled C host executable under WSL / Linux.
  - Axiom PIE executable linking against a `gcc -shared -fPIC` C `.so` and `libc.so.6` (`puts`, `qsort` with an Axiom `extern "C" fn` callback, `errno`), verifying function-pointer address equality across `.so` boundaries (`AMACHINE-79`).
  - Lazy PLT resolution vs eager `BIND_NOW` / full RELRO verification.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_2_linux_elf_dyn` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T660-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T658`–`T659`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:37:00 created by T216 (P16 phase planning)
