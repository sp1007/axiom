---
id: T687
title: E16.10 — Cross-target dynamic library matrix (.dll / .so / .dylib), symbol versioning & .def/import libs
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
priority: 130
status: todo
attempts: 0
depends: [T313, T686, T751]
paths: [compiler/link/dynlib_matrix, compiler/obj/def_import, tests/link/dynlib_matrix, tests/selfhost/obj, tests/selfhost/link]
spec: [spec/SPEC-89-artifact-library-matrix.md, 0164, 0197, 0217, tasks/0369, tasks/0453, tasks/0563]
covers: [REQ-TGT-060, REQ-TGT-104, REQ-TGT-146, REQ-TGT-245, REQ-TGT-246, REQ-TGT-308]
---
# T687 — E16.10 — Cross-target dynamic library matrix (.dll / .so / .dylib), symbol versioning & .def/import libs

## Goal

Implement the unified cross-target dynamic library matrix (`compiler/link/dynlib_matrix`) and module-definition/import-library tooling (`compiler/obj/def_import`) supporting `.dll` + `.lib` + `.def` on Windows, `.so` with `DT_SONAME` and GNU symbol versioning (`VERDEF`/`VERNEED`/`VERSYM`) on Linux/Android, and `.dylib` with `@rpath` install names and version triples on macOS.

## Scope

- Implement `compiler/obj/def_import` and `tests/selfhost/obj/def_import.ax`:
  - Parse and generate Windows `.def` files (ordinals, `NONAME`, `DATA`, forwarded exports `Foo = OTHER.Bar`), COFF short-import `.lib` archives, and ELF/Mach-O export symbol lists.
- Implement `compiler/link/dynlib_matrix` and `tests/selfhost/link/dynlib_matrix.ax`:
  - Emit ELF `.gnu.version` (`SHT_GNU_versym`), `.gnu.version_d` (`SHT_GNU_verdef`), and `.gnu.version_r` (`SHT_GNU_verneed`) sections from Axiom export/version attributes or version scripts.
  - Emit Mach-O `LC_ID_DYLIB`, `LC_RPATH`, `@rpath`/`@loader_path` install names, and re-export `LC_REEXPORT_DYLIB` commands.
  - Enforce hidden-by-default internal symbol visibility (`STV_HIDDEN` / private_extern / non-dllexport) for `cdylib` artifacts unless explicitly exported (`@[export]`).
- Add tests in `tests/link/dynlib_matrix`.

## Acceptance
- [ ] `ctest --output-on-failure -R dynlib_matrix` passes.
- [ ] `cdylib` artifacts export only `@[export]` symbols across PE `.dll`, ELF `.so`, and Mach-O `.dylib`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T687-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
