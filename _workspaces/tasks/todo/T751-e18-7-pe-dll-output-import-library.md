---
id: T751
title: E18.7 PE DLL output: exports, DllMain initialiser, base relocations, import library
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T750]
priority: 701
status: todo
attempts: 0
paths: [compiler/link/pe_dll, compiler/link/implib, tests/link/dll]
spec: [0186, 0187, 0563, 0104, spec/decisions/ADR-0001-fixed-address-declarations.md]
---
# T751 — E18.7 PE DLL output: exports, DllMain initialiser, base relocations, import library

## Goal
`axiomc build --kind dll` produces a PE32+ DLL plus its import library, and Axiom executables can use both our DLLs and third-party DLLs.

## Scope
- `@export` (and `@export("name")`) items → export directory (sorted names, ordinals).
- DLL entry: generated `DllMain`-style initialiser that runs module initialisers on process attach; optional user `@entry` hook; returns FALSE on init failure (also used by E13.7 module-relative bindings).
- Base relocation section (.reloc) so the DLL is relocatable; DYNAMIC_BASE set.
- Import library generation (COFF short import format) alongside the DLL; consumption through T750.

## Acceptance
- [ ] Test: Axiom DLL exporting functions and data; an Axiom exe links its import lib and calls it.
- [ ] Test: exe consuming a third-party DLL built by gcc in fixtures via a generated or provided import lib.
- [ ] objdump -p shows exports, relocations and imports; the DLL still works when rebased.
- [ ] Full test suite passes; outputs byte-identical across two runs.
- [ ] Report `_workspaces/reports/T751-report.md` with exact `## Files changed`.

## Out of scope
- Other targets/formats (ELF/Mach-O libraries are E16.10); Axiom-ABI dynamic components (E20.7).

## Notes
- Owner requirement REQ-OWNER-006, roadmap epic E18.7: implemented in axiomc (Axiom, `compiler/`) right after self-hosting (P18 opens after P10). The C core emits only .obj/.exe but its data models reserve these artifact kinds (SPEC-04, T003a).
- The P18 planning task T218 may split this task; keep this id for the first slice.
- All Axiom code uses canonical syntax (axiom-syntax).
