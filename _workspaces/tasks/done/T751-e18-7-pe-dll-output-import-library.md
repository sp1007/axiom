---
id: T751
title: E18.7 — PE DLL output: exports, DllMain initialiser, base relocations, import library
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T750]
priority: 701
status: done
attempts: 1
paths: [compiler/link, tests/link/dll]
locks: [compiler/obj, compiler/driver, compiler/diag/code.ax, tests/selfhost/link, tests/selfhost/obj, tests/selfhost/driver, tests/selfhost/obj_link_driver, tests/selfhost/diag, tests/selfhost/encode, tests/selfhost/isel, tests/selfhost/backend]
spec: [spec/SPEC-26-windows-artifact-kinds.md, 0186, 0187, tasks/0563, 0104, spec/decisions/ADR-0001-fixed-address-declarations.md, spec/decisions/ADR-0034-oracle-independence-audit.md]
covers: [REQ-OWNER-006, REQ-LNK-073, REQ-LNK-074, REQ-LNK-075, REQ-LNK-076, REQ-LNK-077, REQ-LNK-078, REQ-LNK-079, REQ-LNK-080, REQ-LNK-081, REQ-LNK-082, REQ-LNK-083, REQ-LNK-084, REQ-LNK-085, REQ-LNK-086, REQ-LNK-087, REQ-LNK-088, REQ-LNK-089, REQ-LNK-090, REQ-LNK-091, REQ-LNK-092, REQ-LNK-093, REQ-LNK-094, REQ-LNK-095, REQ-LNK-096, REQ-LNK-097, REQ-LNK-098, REQ-LNK-099, REQ-LNK-100, REQ-LNK-101, REQ-LNK-102, REQ-LNK-103, REQ-LNK-104, REQ-LNK-105, REQ-LNK-106, REQ-LNK-107, REQ-LNK-108, REQ-LNK-109, REQ-LNK-110, REQ-LNK-111, REQ-LNK-112]
started: 2026-11-05 07:15:30
finished: 2026-11-06 00:33:54
---
# T751 — E18.7 — PE DLL output: exports, DllMain initialiser, base relocations, import library

## Goal
`axiomc build --kind dll` produces a PE32+ DLL plus its import library, and Axiom executables can use both our DLLs and third-party DLLs per `spec/SPEC-26-windows-artifact-kinds.md`.

## Scope
- `@export` (and `@export("name")`) items → `.edata` export directory (sorted names, ordinals).
- DLL entry: generated `DllMain`-style initialiser that runs module initialisers on process attach; optional user `@entry` hook; returns `FALSE` on init failure (also used by E13.7 module-relative bindings, `ADR-0001` §5–6).
- Base relocation section (`.reloc`) so the DLL is relocatable; `DYNAMIC_BASE` set.
- Import library generation (COFF short import format) alongside the DLL; consumption through `T750`; `--emit=obj` references imports via standard `__imp_<name>` and ships runtime object support so GNU `ld`/`gcc` can cross-link real Axiom programs (`ADR-0034` §4 OI-07b).

## Acceptance
- [ ] Test: Axiom DLL exporting functions and data; an Axiom exe links its import lib and calls it.
- [ ] Test: exe consuming a third-party DLL built by `gcc` in fixtures via a generated or provided import lib.
- [ ] `objdump -p` shows exports, relocations and imports; the DLL still works when rebased.
- [ ] Carry-over oracle (`ADR-0034` §4 OI-07b): native run tests emitted with `--emit=obj` and linked by GNU `ld` run identically to self-linked PE executables.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); outputs byte-identical across two runs.
- [ ] Report `_workspaces/reports/T751-report.md` with exact `## Files changed`.

## Out of scope
- Other targets/formats (ELF/Mach-O libraries are E16.10); Axiom-ABI dynamic components (E20.7).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Owner requirement `REQ-OWNER-006`, roadmap epic E18.7: implemented in `axiomc` (Axiom, `compiler/`) right after self-hosting (P18 opens after P10). The C core emits only `.obj`/`.exe` but its data models reserve these artifact kinds (SPEC-04, T003a).
- Carry-over (ADR-0034 §4, audit 2026-10-19 OI-07b): with import libraries, `--emit=obj` must reference imports as standard `__imp_<name>` and ship the runtime as a linkable object, so that `gcc`/`ld` can link real Axiom programs; add the deferred T028 oracle here — every native run test linked by GNU `ld` runs like the self-linked PE.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T751/build` and `python tools/axtest.py --compiler build-snap-T751/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom code uses canonical syntax (`axiom-syntax`).

## Log
- 2026-10-06 02:24:26 covers += REQ-OWNER-006 (metadata only)
- 2026-11-03 03:00:20 refined by T218 (linked to SPEC-26 and T773)
- 2026-11-05 07:15:30 started (attempt 1) T751-impl
- 2026-11-06 00:33:54 accepted by QA -> done
