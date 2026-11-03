---
id: T686
title: E16.10 — Cross-target static archive (.a / .lib / axlib) producer & consumer
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
priority: 129
status: todo
attempts: 0
depends: [T313, T659, T667, T675, T679, T685, T750]
paths: [compiler/obj/archive_matrix, compiler/link/archive_resolve, tests/link/static_matrix, tests/selfhost/obj, tests/selfhost/link]
spec: [spec/SPEC-89-artifact-library-matrix.md, 0164, 0217, tasks/0369, tasks/0453, tasks/0563]
covers: [REQ-TOOL-001, REQ-TGT-101, REQ-TGT-151, REQ-TGT-184, REQ-TGT-247]
---
# T686 — E16.10 — Cross-target static archive (.a / .lib / axlib) producer & consumer

## Goal

Implement the unified cross-target static archive producer (`compiler/obj/archive_matrix`) and linker archive resolver (`compiler/link/archive_resolve`) supporting GNU/SysV `.a`, BSD/Darwin `__.SYMDEF SORTED` `.a`, COFF `.lib`, and Axiom `.axlib` (with `.axrmeta` interface metadata) across both `axiom0` and the self-hosted compiler.

## Scope

- Implement `compiler/obj/archive_matrix` and `tests/selfhost/obj/archive_matrix.ax`:
  - Emit deterministic `!<arch>\n` archives with GNU `/` symbol table + `//` long filename table (for ELF/COFF) and BSD `__.SYMDEF SORTED` + `#1/<len>` extended filenames (for Darwin Mach-O).
  - Embed `.axrmeta` serialized module interface and generic MIR bodies for `axlib` artifacts.
  - Zero timestamps, UID, GID, and normalize file modes for bit-identical reproducibility.
- Implement `compiler/link/archive_resolve` and `tests/selfhost/link/archive_resolve.ax`:
  - Iterative worklist-driven symbol resolution across `.a`/`.lib`/`.axlib` archives, `--whole-archive` / `--no-whole-archive` flags, and thin-archive rejection/diagnostics.
- Add unit tests in `tests/link/static_matrix`.

## Acceptance
- [ ] `ctest --output-on-failure -R static_matrix` passes.
- [ ] Produced `.a` and `.lib` archives are byte-identical across repeated builds and consumable by both Axiom's internal linkers and host `ar`/`ranlib`/`llvm-ar`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T686-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
