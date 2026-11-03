---
id: T706
title: E17.2 DWARF v5 .debug_loclists/.debug_rnglists/.debug_names, ELF build-id, Mach-O __DWARF/.dSYM & WASM debug linker
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T705]
priority: 176
status: todo
attempts: 0
paths: [compiler/link/dwarf, tests/run/debug/dwarf]
spec: [spec/SPEC-93-dwarf-elf-macho.md, tasks/0596, tasks/0525, tasks/0419]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T706 — E17.2 DWARF v5 .debug_loclists/.debug_rnglists/.debug_names, ELF build-id, Mach-O __DWARF/.dSYM & WASM debug linker

## Goal
Implement DWARF v5 location/range/accelerator tables (.debug_loclists, .debug_rnglists, .debug_names) and link DWARF debug sections across ELF binaries, Mach-O .dSYM bundles, and WASM modules.

## Scope
- Implement `.debug_loclists` (`DW_LLE_offset_pair`, `DW_LLE_base_addressx`, `DW_OP_reg*`, `DW_OP_fbreg`, `DW_OP_piece`, `DW_OP_stack_value`) and `.debug_rnglists` (`DW_RLE_offset_pair`, `DW_RLE_startx_length`) plus `.debug_names` accelerator tables in `compiler/link/dwarf`.
- Integrate DWARF v5 section relocation and merging into the ELF linker (with deterministic `.note.gnu.build-id` and optional `--split-debug` `.debug`/`.gnu_debuglink`), the Mach-O linker (`__DWARF` segment and companion `.dSYM` bundle generator with matching `LC_UUID`), and the WASM32 module writer (custom `.debug_*` sections with code-section-relative offsets).
- Add end-to-end DWARF linking and inspection tests in `tests/run/debug/dwarf`.

## Acceptance
- [ ] `axiomc build -g` emits valid DWARF v5 sections in ELF (`x86_64-linux`, `aarch64-linux`, `riscv64-linux`), Mach-O `.dSYM` (`aarch64-macos`), and WASM (`wasm32`) binaries.
- [ ] Repeated `axiomc build -g` runs produce byte-identical DWARF outputs and matching build-ID / `LC_UUID` digests.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T706-report.md` with exact `## Files changed`.

## Out of scope
- Unwind tables `.eh_frame`/`.eh_frame_hdr` and Mach-O `__unwind_info` (`T709`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
