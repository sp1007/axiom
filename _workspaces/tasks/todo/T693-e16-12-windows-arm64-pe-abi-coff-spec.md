---
id: T693
title: E16.12 — Windows ARM64 (aarch64-pc-windows-msvc) PE/COFF & ABI specification (SPEC-91)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
priority: 136
status: todo
attempts: 0
depends: [T216, T313, T661, T772]
paths: [spec/SPEC-91-windows-arm64.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-26-windows-artifact-kinds.md, spec/SPEC-83-aarch64-linux.md, 0181, 0185, 0186, 0187, 0193, tasks/0453, tasks/0521]
covers: [REQ-TGT-114, REQ-TGT-124, REQ-TGT-127, REQ-TGT-129]
---
# T693 — E16.12 — Windows ARM64 (aarch64-pc-windows-msvc) PE/COFF & ABI specification (SPEC-91)

## Goal

Author `spec/SPEC-91-windows-arm64.md` — the normative specification for Axiom's `aarch64-pc-windows-msvc` target, covering the Windows ARM64 calling convention delta from AAPCS64, `x18` TEB platform register reservation, `__chkstk` stack probing protocol (`x15` page-count in 16-byte units), COFF `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) relocations, `.pdata`/`.xdata` ARM64 packed and unpacked unwind data, and PE32+ ARM64 executable/DLL linking.

## Scope

- Create `spec/SPEC-91-windows-arm64.md` covering:
  - Windows ARM64 ABI deltas vs Linux AAPCS64: variadic functions pass all arguments in integer registers `x0`–`x7` and on the stack (never `v0`–`v7`), `x18` strictly reserved for the Thread Environment Block (`TEB`), and C++/POD return-value rules.
  - Stack probing protocol: `__chkstk` receives allocation size divided by 16 in `x15`, clobbers `x16`/`x17`/`nzcv`, and preserves `sp` (caller subtracts `sp, sp, x15, lsl #4` after `bl __chkstk`).
  - COFF `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) object format and relocation types (`IMAGE_REL_ARM64_ADDR32`, `ADDR64`, `BRANCH26`, `PAGEBASE_REL21`, `PAGEOFFSET_12A`, `PAGEOFFSET_12L`, `SECREL`, `REL32`).
  - Windows ARM64 `.pdata` (8-byte runtime function entries supporting packed unwind info in `Flag` bits) and `.xdata` unwind codes (`alloc_s`, `alloc_m`, `alloc_l`, `save_fplr`, `save_fplr_x`, `save_r19r20_x`, `save_reg`, `save_regp`, `save_freg`, `set_fp`, `end`).
  - PE32+ ARM64 executable and DLL linking, import thunks (`adrp x16, __imp_Foo` + `ldr x16, [x16, #:lo12:__imp_Foo]` + `br x16`), and TLS directory access via `x18` (`TEB + 0x58`).
- Register `SPEC-91`, diagnostics (`E9100–E9119`), and invariants (`INV-WIN-ARM64-01..05`) in `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `python .claude/skills/axiom-tasks/scripts/harness_check.py` exits 0.
- [ ] `spec/SPEC-91-windows-arm64.md` defines all Windows ARM64 ABI, COFF, unwind, and PE32+ linking contracts.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T693-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
