---
id: T711
title: E17.4 Canonical AXDEBUGGER contract, symbolication engine & semantic visualization specification (SPEC-95)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316, T700, T704, T708]
priority: 182
status: todo
attempts: 0
paths: [spec/SPEC-95-debugger-contract-symbolication.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-92-debug-ir-codeview-pdb.md, spec/SPEC-93-dwarf-elf-macho.md, spec/SPEC-94-unwinding-backtraces.md, 0100, 0147, tasks/0811, tasks/1055, tasks/0596]
covers: [REQ-DBG-116, REQ-DBG-118, REQ-DBG-120]
---
# T711 — E17.4 Canonical AXDEBUGGER contract, symbolication engine & semantic visualization specification (SPEC-95)

## Goal
Consolidate the canonical specification for Axiom native debugger interop (WinDbg/cdb, GDB, LLDB), the cross-format symbolication engine, inline/async logical frame reconstruction, and semantic type visualizers into spec/SPEC-95-debugger-contract-symbolication.md (AXS-DBGC-* rules).

## Scope
- Write `spec/SPEC-95-debugger-contract-symbolication.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-DBGC-NNN` rules.
- Specify the native debugger contract (`0100 §9–19`, `0147 §1–15`, `tasks/0811 §589`, `tasks/1055`): standard platform debuggers (`cdb`/`WinDbg` on Windows via CodeView/PDB, `gdb`/`lldb` on Linux/macOS via DWARF v5) work out of the box without a proprietary debug protocol; Axiom-aware mode layers semantic provenance (`SourceOrigin`, ownership/capability state `Owned`/`Moved`/`View`/`MutView`, async state machines) on top of standard DWARF/PDB artifacts (`ADEBUG-81`..`ADEBUG-84`).
- Specify the cross-format symbolication engine (`tasks/0596`, `tasks/0811 §589.160–173`): resolving `(module_build_id, rva)` to demangled Axiom function path, canonical `file:line:col`, logical inline call chain (`S_INLINESITE` / `DW_TAG_inlined_subroutine`), async `Future` suspension chain, and build-ID / source-hash mismatch warnings (`0811 §589.193–195`, `ADEBUG-96`).
- Specify embedded Natvis (`.natvis` PDB stream) and GDB/LLDB Python visualizers (`.debug_gdb_scripts`) for Axiom `str`, `String`, `Vec<T>`, `Slice<T>`, `HashMap<K,V>`, `Option<T>`, `Result<T,E>`, niche enums, and `Future` state machines, plus secret/redacted type masking (`@secret` / `Secret<T>` displays `<redacted>` per `ADEBUG-88`/`ADEBUG-89`).
- Specify the `axiomc symbolicate` and `axiomc debug` CLI interface (`0811 §589.174–182`, `1055`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-95-debugger-contract-symbolication.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-DBGC-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T711-report.md` with exact `## Files changed`.

## Out of scope
- Symbolication engine and visualizer implementation (`T712`, `T713`, `T714`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
