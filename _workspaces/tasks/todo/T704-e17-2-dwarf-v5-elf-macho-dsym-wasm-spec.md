---
id: T704
title: E17.2 Canonical DWARF v5 debug sections, line programs, location lists & Mach-O dSYM/WASM debug specification (SPEC-93)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316, T700]
priority: 174
status: todo
attempts: 0
paths: [spec/SPEC-93-dwarf-elf-macho.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-92-debug-ir-codeview-pdb.md, tasks/0596, tasks/0525, tasks/0419]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T704 — E17.2 Canonical DWARF v5 debug sections, line programs, location lists & Mach-O dSYM/WASM debug specification (SPEC-93)

## Goal
Consolidate the canonical specification for lowering Axiom Debug IR to DWARF v5 across ELF, Mach-O (.dSYM), and WASM targets into spec/SPEC-93-dwarf-elf-macho.md (AXS-DWRF-* rules).

## Scope
- Write `spec/SPEC-93-dwarf-elf-macho.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-DWRF-NNN` rules.
- Specify the target-independent `DebugIR` → DWARF v5 lowering contract (`ADBG-32`, `ADEBUG-79`, `ADEBUG-80`): zero changes to frontend/semantic stages, deterministic DIE ordering (`ADEBUG-64`), and source path remapping (`--remap-path-prefix`, `ADEBUG-63`).
- Specify DWARF v5 sections (`.debug_info`, `.debug_abbrev`, `.debug_str`, `.debug_line_str`, `.debug_line`, `.debug_loclists`, `.debug_rnglists`, `.debug_aranges`, `.debug_names`): DIE representation of Axiom primitives, structs, `DW_TAG_variant_part` enums (including niche-optimized `Option`/`Result` per `ADEBUG-33`/`ADEBUG-34`), slices/views, closures (`ADEBUG-46`), generic instantiations (`ADEBUG-35`/`ADEBUG-36`), `DW_TAG_inlined_subroutine` (`ADEBUG-37`/`ADEBUG-38`), and `Future` async state fields (`ADEBUG-44`/`ADEBUG-45`).
- Specify DWARF v5 location and range lists: `DW_LLE_offset_pair` with `DW_OP_reg*`, `DW_OP_breg*`, `DW_OP_fbreg`, `DW_OP_piece` composite locations (`ADEBUG-30`), `DW_OP_stack_value` constant/rematerialized SSA values, and omitted location ranges for `<optimized out>` values (`ADEBUG-28`).
- Specify container packaging across ELF (`ET_REL`/`ET_EXEC`/`ET_DYN`, `.note.gnu.build-id`, `.gnu_debuglink` split debug), Mach-O (`__DWARF` object sections, `.dSYM` bundle layout with matching `LC_UUID`), and WASM (`wasm32` custom `.debug_*` sections with code-section-relative offsets per `ADEBUG-77`/`ADEBUG-78`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-93-dwarf-elf-macho.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-DWRF-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T704-report.md` with exact `## Files changed`.

## Out of scope
- DWARF object and linker implementation (`T705`, `T706`, `T707`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
