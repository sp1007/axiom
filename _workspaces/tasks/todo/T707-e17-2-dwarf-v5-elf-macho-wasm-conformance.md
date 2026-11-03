---
id: T707
title: E17.2 DWARF v5 ELF, Mach-O .dSYM & WASM debug information conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T217, T316, T706]
priority: 177
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_2_dwarf]
spec: [spec/SPEC-93-dwarf-elf-macho.md, tasks/0596, tasks/0525, tasks/0419]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T707 — E17.2 DWARF v5 ELF, Mach-O .dSYM & WASM debug information conformance suite

## Goal
Certify the E17.2 exit criteria: DWARF v5 completeness, accuracy under optimization, and cross-target container compliance across ELF, Mach-O (.dSYM), and WASM.

## Scope
- Create `tests/conformance/p17/e17_2_dwarf` covering:
-   - DWARF v5 `.debug_info`, `.debug_abbrev`, `.debug_line`, `.debug_loclists`, `.debug_rnglists`, and `.debug_names` verification across `x86_64-linux`, `aarch64-linux`, `riscv64-linux`, `aarch64-macos`, and `wasm32`.
-   - Variable location tracking across register allocation spills, composite `DW_OP_piece` values, `DW_OP_stack_value` constant folding, and `<optimized out>` omission at `-O2`.
-   - Axiom enum `DW_TAG_variant_part` (including niche-optimized `Option`/`Result`), generic monomorphization provenance, closure capture provenance, and `DW_TAG_inlined_subroutine` call chains.
-   - Binary-to-debug build-ID (`.note.gnu.build-id` / `LC_UUID`), `--remap-path-prefix` reproducibility, and `-g` vs stripped codegen invariance.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p17/e17_2_dwarf` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T707-report.md` with exact `## Files changed`.

## Out of scope
- CodeView/PDB tests (`T703`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
