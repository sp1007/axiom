---
id: T688
title: E16.10 — Artifact & library matrix conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
priority: 131
status: todo
attempts: 0
depends: [T313, T687]
paths: [tests/conformance/p16/e16_10_artifact_matrix]
spec: [spec/SPEC-89-artifact-library-matrix.md, 0164, 0197, 0217, tasks/0369, tasks/0453, tasks/0563]
covers: [REQ-TGT-106, REQ-TGT-307, REQ-TGT-308, REQ-TGT-318, REQ-TGT-320]
---
# T688 — E16.10 — Artifact & library matrix conformance suite

## Goal

Build the end-to-end conformance suite (`tests/conformance/p16/e16_10_artifact_matrix`) verifying every artifact kind (`exe`, `staticlib`, `cdylib`, `axlib`, `obj`, `wasm-module`) across all supported targets, diamond library dependency graphs, symbol visibility isolation, and deterministic archive/shared-library emission.

## Scope

- Create `tests/conformance/p16/e16_10_artifact_matrix` testing:
  - Cross-target matrix emitting `exe`, `staticlib`, `cdylib`, `axlib`, and `obj` for Windows x64, Linux x64/AArch64/RISC-V64, macOS AArch64, Android AArch64, and WASM32.
  - Diamond dependency graphs combining `axlib` + `staticlib` + `cdylib` with duplicate symbol diagnostics (`E8900–E8919`) and `--whole-archive` overrides.
  - Symbol visibility verification confirming non-exported symbols do not leak into `.dynsym`, PE export tables, or Mach-O export tries.
  - Byte-for-byte reproducibility of `.a`, `.lib`, `.axlib`, `.so`, `.dll`, and `.dylib` outputs across repeated builds.

## Acceptance
- [ ] `ctest --output-on-failure -R e16_10_artifact_matrix` passes 100%.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T688-report.md` with exact `## Files changed`.

## Out of scope
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom sources and test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin ch?o th? gi?i` for greeting strings.

## Log
- 2026-11-03 08:50:00 created by T216 (P16 phase planning)
