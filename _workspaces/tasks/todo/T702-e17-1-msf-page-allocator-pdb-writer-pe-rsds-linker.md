---
id: T702
title: E17.1 Deterministic MSF v7 page allocator, PDB 7.00 stream writer & PE RSDS debug directory linker
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T701]
priority: 172
status: todo
attempts: 0
paths: [compiler/link/pdb, compiler/link/pe_debug, tests/run/debug/pdb]
spec: [spec/SPEC-92-debug-ir-codeview-pdb.md, 0190, 0191, tasks/0525]
covers: [REQ-DBG-117, REQ-DBG-118]
---
# T702 — E17.1 Deterministic MSF v7 page allocator, PDB 7.00 stream writer & PE RSDS debug directory linker

## Goal
Implement the deterministic MSF v7 multi-stream container, PDB 7.00 stream builder (PDB Info, TPI, DBI, IPI, Publics/Globals, Section Headers), and PE IMAGE_DIRECTORY_ENTRY_DEBUG RSDS linker integration.

## Scope
- Implement the MSF v7 container writer in `compiler/link/pdb` (`Microsoft C/C++ MSF 7.00` superblock, 4096-byte block size, FPM1/FPM2 free-page maps, and two-phase deterministic stream directory allocator).
- Implement the PDB 7.00 streams in `compiler/link/pdb`: Stream 1 (PDB Info with deterministic content-derived GUID and `Age = 1`), Stream 2 (TPI merged type records + hash stream), Stream 3 (DBI module descriptors, section contribution table, section map, file info substream), Stream 4 (IPI merged ID records), Global/Public hashed symbol streams (GSI/PSI), and per-module C13 symbol/line streams relocated to final PE RVAs.
- Implement `compiler/link/pe_debug` emitting `.rdata` `IMAGE_DEBUG_DIRECTORY` (`IMAGE_DEBUG_TYPE_CODEVIEW` with `RSDS` signature, matching 16-byte GUID, `Age = 1`, and `.pdb` path) and wiring `axiomc build -g` for PE `.exe` and `.dll` targets.
- Add end-to-end PDB generation and structural inspection tests in `tests/run/debug/pdb`.

## Acceptance
- [ ] `axiomc build -g` on Windows emits a `.exe`/`.dll` and companion `.pdb` with matching `RSDS` GUID/Age and valid MSF/TPI/IPI/DBI/Publics streams.
- [ ] Repeated `axiomc build -g` runs on identical sources produce byte-identical `.exe` and `.pdb` files (`0191 §12–15`, `ADBG-34`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T702-report.md` with exact `## Files changed`.

## Out of scope
- DWARF v5 debug emission (`E17.2`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
