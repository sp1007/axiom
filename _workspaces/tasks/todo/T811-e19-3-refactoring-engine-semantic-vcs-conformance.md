---
id: T811
title: E19.3 Semantic refactoring engine, code actions & AXDIFF/AXMERGE/AXPATCH/AXHISTORY/AXVCS conformance suite
phase: P19-developer-tooling
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T219, T318, T810]
priority: 201
status: todo
attempts: 0
paths: [tests/conformance/p19/e19_3_refactoring_vcs]
spec: [spec/SPEC-102-refactoring-engine-semantic-vcs.md, 0101, tasks/0448, tasks/1059, tasks/1060, tasks/1061, tasks/1062, tasks/1063, tasks/1064]
covers: [REQ-TOOL-183, REQ-TOOL-186, REQ-TOOL-301, REQ-TOOL-302, REQ-TOOL-303, REQ-TOOL-304, REQ-TOOL-305]
---
# T811 — E19.3 Semantic refactoring engine, code actions & AXDIFF/AXMERGE/AXPATCH/AXHISTORY/AXVCS conformance suite

## Goal
Certify E19.3 exit criteria with an end-to-end conformance suite covering `CompilerDB` refactoring transformations, LSP code actions, and `AXDIFF`/`AXMERGE`/`AXPATCH`/`AXHISTORY`/`AXVCS`.

## Scope
- Create conformance tests in `tests/conformance/p19/e19_3_refactoring_vcs` verifying:
  - semantics preservation (identical `--interp` and native execution outputs before and after refactoring) across extract-function, extract/inline-binding, exhaustive-match completion, and import canonicalization;
  - `CompilerDB` rejection of invalid refactorings that would violate ownership or `view`/`mut_view` capability rules (`REQ-TOOL-186`);
  - `AXDIFF` AST diffing (`REQ-TOOL-301`), `AXMERGE` 3-way semantic merge (`REQ-TOOL-302`), `AXPATCH` AST/text patching (`REQ-TOOL-303`), `AXHISTORY` refactoring lineage (`REQ-TOOL-304`), and `AXVCS` deterministic ordering (`REQ-TOOL-305`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p19/e19_3_refactoring_vcs` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T811-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T811/build` and `python tools/axtest.py --compiler build-snap-T811/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
