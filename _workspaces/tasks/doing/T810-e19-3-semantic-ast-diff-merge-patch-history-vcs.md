---
id: T810
title: E19.3 Semantic AST diff/merge/patch & lineage history engine (AXDIFF, AXMERGE, AXPATCH, AXHISTORY, AXVCS)
phase: P19-developer-tooling
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T805, T809]
priority: 200
status: doing
attempts: 1
paths: [compiler/refactor/vcs, std/vcs, compiler/driver/refactor_cmd, tests/run/semantic_vcs]
spec: [spec/SPEC-102-refactoring-engine-semantic-vcs.md, 0101, tasks/1059, tasks/1060, tasks/1061, tasks/1062, tasks/1063, tasks/1064]
covers: [REQ-TOOL-301, REQ-TOOL-302, REQ-TOOL-303, REQ-TOOL-304, REQ-TOOL-305]
started: 2026-11-08 16:34:39
agent: T810-impl
---
# T810 — E19.3 Semantic AST diff/merge/patch & lineage history engine (AXDIFF, AXMERGE, AXPATCH, AXHISTORY, AXVCS)

## Goal
Implement the semantic-aware `AXDIFF`, `AXMERGE`, `AXPATCH`, `AXHISTORY`, and `AXVCS` engines and CLI commands in `compiler/refactor/vcs`, `std/vcs`, and `compiler/driver/refactor_cmd` per `spec/SPEC-102-refactoring-engine-semantic-vcs.md`.

## Scope
- Implement `AXDIFF` (`compiler/refactor/vcs/diff.ax`): structural CST/AST and `CompilerDB` symbol diffing (`0101 §45`, `tasks/1059`, `REQ-TOOL-301`) that classifies trivia/formatting-only edits, item relocations, renames, and semantic signature/API changes.
- Implement `AXMERGE` (`compiler/refactor/vcs/merge.ax`) and `AXPATCH` (`compiler/refactor/vcs/patch.ax`): AST-aware 3-way merge resolving non-overlapping declaration/import/block edits (`tasks/1060`, `REQ-TOOL-302`) and transactional AST + text patch application with content-hash precondition checks (`tasks/1061`, `tasks/1064`, `REQ-TOOL-303`).
- Implement `AXHISTORY` and `AXVCS` (`std/vcs`, `compiler/driver/refactor_cmd`): deterministic content-addressed semantic repository store (`REQ-TOOL-305`) and symbol/refactoring lineage tracker across revisions (`tasks/1062`, `tasks/1063`, `REQ-TOOL-304`), exposed via `axiomc refactor`, `axiomc diff`, `axiomc merge`, and `axiomc patch`.

## Acceptance
- [ ] Run tests in `tests/run/semantic_vcs` verify `AXDIFF` tree vs text comparison, `AXMERGE` AST-aware conflict resolution and semantic conflict detection, `AXPATCH` atomic application/rollback, `AXHISTORY` symbol lineage across renames/extractions, and `AXVCS` deterministic snapshot ordering.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T810-report.md` with exact `## Files changed`.

## Out of scope
- Diagnostics UX 2.0 and `axiomc explain` (`T812`–`T815`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T810/build` and `python tools/axtest.py --compiler build-snap-T810/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 16:34:39 started (attempt 1) T810-impl
