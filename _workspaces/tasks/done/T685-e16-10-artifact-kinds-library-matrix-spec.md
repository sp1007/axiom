---
id: T685
title: E16.10 — Artifact kinds & library matrix specification (SPEC-89)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
priority: 128
status: done
attempts: 1
depends: [T216, T511, T657, T665, T772]
paths: [spec/SPEC-89-artifact-library-matrix.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, spec/SPEC-26-windows-artifact-kinds.md, spec/SPEC-82-linux-elf-dynamic.md, spec/SPEC-84-macos-aarch64-macho.md, 0164, 0197, 0217, tasks/0369, tasks/0453, tasks/0563]
covers: [REQ-TGT-101, REQ-TGT-103, REQ-TGT-104, REQ-TGT-184, REQ-TGT-307, REQ-TGT-308]
started: 2026-11-04 05:52:26
finished: 2026-11-04 06:53:27
---
# T685 — E16.10 — Artifact kinds & library matrix specification (SPEC-89)

## Goal

Author `spec/SPEC-89-artifact-library-matrix.md` — the normative specification for Axiom's cross-target artifact kinds (`exe`, `staticlib`, `cdylib`, `rlib`/`axlib`, `obj`, `wasm-module`) and library consumption/production matrix across PE/COFF (`.exe`/`.dll`/`.lib`/`.def`), ELF64 (`.a`/`.so`/PIE), Mach-O (`.a`/`.dylib`/`.app` binary), and WebAssembly (`.wasm`), including symbol versioning, export control, and reproducible archive rules.

## Scope

- Create `spec/SPEC-89-artifact-library-matrix.md` covering:
  - Canonical `--crate-type` / `artifact_kind` matrix (`bin`/`exe`, `staticlib`, `cdylib`, `lib`/`axlib`, `obj`) across all Tier-1 and Tier-2 targets.
  - Static archive format rules: BSD vs GNU/SysV `/` string table and symbol index (`SYMDEF` on Darwin, `/` + `//` on ELF/COFF), deterministic zeroed timestamps/UID/GID/mode (`0644`), and `.axrmeta` metadata member layout for `axlib`.
  - Dynamic library production & consumption matrix: Windows `.dll` + `.lib` import library + `.def` module definition files; Linux `.so` with `DT_SONAME`, GNU version scripts (`VERDEF`/`VERNEED`/`VERSYM`), and `STB_GLOBAL`/`STV_DEFAULT` export lists; macOS `.dylib` with `LC_ID_DYLIB`, `@rpath`/`@loader_path`/`@executable_path` install names, and compatibility/current versions; WASM reactor modules (`_initialize`).
  - Whole-archive vs demand-driven archive member extraction semantics, duplicate symbol resolution diagnostics, and LTO bitcode/MIR section embedding.
- Register `SPEC-89`, diagnostics (`E8900–E8919`), and invariants (`INV-ART-01..05`) in `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `python .claude/skills/axiom-tasks/scripts/harness_check.py` exits 0.
- [ ] `spec/SPEC-89-artifact-library-matrix.md` defines all artifact kinds and cross-target library rules.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T685-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
- 2026-11-04 05:52:26 started (attempt 1) T685-impl
- 2026-11-04 06:53:27 accepted by QA -> done
