---
id: T765
title: E18.4 — Module interface metadata (.axmi) serializer, loader & exported symbol/generic summaries
phase: P18-compiler-architecture-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T764, T753]
priority: 715
status: doing
attempts: 1
paths: [compiler/artifact/axmi, tests/run/artifact_axmi]
spec: [spec/SPEC-24-artifact-format-module-interfaces.md, tasks/0582, tasks/0739, tasks/0787]
covers: [REQ-LNK-504, REQ-LNK-505, REQ-LNK-506, REQ-LNK-507, REQ-LNK-508, REQ-LNK-509, REQ-LNK-510, REQ-LNK-511, REQ-LNK-512, REQ-LNK-513, REQ-LNK-514, REQ-LNK-515, REQ-LNK-516, REQ-LNK-517, REQ-LNK-518, REQ-LNK-519, REQ-LNK-520, REQ-LNK-521, REQ-LNK-522, REQ-LNK-523, REQ-LNK-524, REQ-LNK-525, REQ-LNK-526, REQ-LNK-527, REQ-LNK-528, REQ-LNK-529, REQ-LNK-530, REQ-LNK-531, REQ-LNK-532, REQ-LNK-533, REQ-LNK-534, REQ-LNK-535, REQ-LNK-536, REQ-LNK-537, REQ-LNK-538, REQ-LNK-539, REQ-LNK-540, REQ-LNK-541, REQ-LNK-542, REQ-LNK-543, REQ-LNK-544, REQ-LNK-545, REQ-LNK-546, REQ-LNK-547, REQ-LNK-548, REQ-LNK-549, REQ-LNK-550, REQ-LNK-551, REQ-LNK-552, REQ-LNK-553, REQ-LNK-554, REQ-LNK-555, REQ-LNK-556, REQ-LNK-557, REQ-LNK-558, REQ-LNK-559, REQ-LNK-560, REQ-LNK-561, REQ-LNK-562, REQ-LNK-563, REQ-LNK-564, REQ-LNK-565, REQ-LNK-566, REQ-LNK-567, REQ-LNK-568, REQ-LNK-569, REQ-LNK-570, REQ-LNK-571, REQ-LNK-572, REQ-LNK-573]
started: 2026-11-07 20:59:35
agent: T765-impl
---
# T765 — E18.4 — Module interface metadata (.axmi) serializer, loader & exported symbol/generic summaries

## Goal
Implement deterministic `.axmi` module interface emission and loading in `compiler/artifact/axmi` so downstream modules resolve types, traits, capabilities, `const` items, and generic templates directly from `.axmi` without upstream `.ax` source files per `spec/SPEC-24-artifact-format-module-interfaces.md`.

## Scope
- Implement `.axmi` binary serialization and deserialization in `compiler/artifact/axmi` covering exported item signatures, type definitions, trait/impl tables, ownership/capability contracts (`tasks/0582`), and serialized generic/inlineable MIR templates (`tasks/0739`, `tasks/0787`).
- Integrate `.axmi` loading into `CompilerDB` (`T753`–`T754`) so importing a compiled module populates declaration/signature queries directly from `.axmi`.
- Add `--emit=axmi` and `inspect --axmi <file>` to dump module interface contents deterministically.

## Acceptance
- [ ] Tests in `tests/run/artifact_axmi` compile an upstream module to `.axmi` + `.obj`, delete/hide the upstream `.ax` source, and compile a downstream consumer using only `.axmi` + `.obj` (including generic instantiation and cross-module `const` use).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T765-report.md` with exact `## Files changed`.

## Out of scope
- Embedded object/LTO sections and archive container packaging (`T766`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T765/build` and `python tools/axtest.py --compiler build-snap-T765/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:55 created by T218 (P18 phase planning)
- 2026-11-07 20:59:35 started (attempt 1) T765-impl
