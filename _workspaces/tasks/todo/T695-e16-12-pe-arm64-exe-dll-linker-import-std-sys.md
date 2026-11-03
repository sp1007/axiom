---
id: T695
title: E16.12 — PE32+ ARM64 executable/DLL linker, import thunks & std.sys.windows.arm64
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
priority: 138
status: todo
attempts: 0
depends: [T313, T687, T694, T751]
paths: [compiler/link/pe_arm64, std/sys/windows/arm64, tests/link/pe_arm64, tests/selfhost/link]
spec: [spec/SPEC-91-windows-arm64.md, 0181, 0186, 0187, 0193, tasks/0453]
covers: [REQ-TGT-104, REQ-TGT-124, REQ-TGT-151, REQ-TGT-152, REQ-TGT-308]
---
# T695 — E16.12 — PE32+ ARM64 executable/DLL linker, import thunks & std.sys.windows.arm64

## Goal

Implement the PE32+ ARM64 (`0xAA64`) executable and DLL linker (`compiler/link/pe_arm64`) with ARM64 IAT import thunks, base relocations, and `.pdata` sorting, along with `std.sys.windows.arm64` startup/TEB/intrinsic bindings.

## Scope

- Implement `compiler/link/pe_arm64` and `tests/selfhost/link/pe_arm64.ax`:
  - Resolve `IMAGE_REL_ARM64_BRANCH26` (emitting range-extension veneer islands when branch targets exceed ±128 MiB), `PAGEBASE_REL21`, `PAGEOFFSET_12A`/`12L`, `ADDR64`, `ADDR32NB`, and `SECREL`.
  - Synthesize ARM64 DLL import thunks (`adrp x16, __imp_<sym>; ldr x16, [x16, #:lo12:__imp_<sym>]; br x16`), `.idata` Import Directory / IAT, `.edata` Export Directory, `.reloc` (`IMAGE_REL_BASED_DIR64`), and RVA-sorted `.pdata` Exception Directory.
  - Provide built-in `__chkstk` implementation for freestanding/no-CRTPE binaries.
- Implement `std/sys/windows/arm64`:
  - Provide `aarch64-pc-windows-msvc` startup (`mainCRTStartup` / `DllMainCRTStartup`), TEB access via `x18` (`NtCurrentTeb()`), implicit TLS (`_tls_index` via `[x18, #0x58]`), and ARM64 Win32 `kernel32.dll` bindings.
- Add linker tests in `tests/link/pe_arm64`.

## Acceptance
- [ ] `ctest --output-on-failure -R pe_arm64` passes.
- [ ] Linked `.exe` and `.dll` binaries pass PE32+ `0xAA64` header, IAT/EAT, `.reloc`, and sorted `.pdata` validation.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T695-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
