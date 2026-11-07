---
id: T763
title: E18.3 — Parallel compilation thread-count invariance & byte-identical determinism conformance suite
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T762]
priority: 713
status: doing
attempts: 1
paths: [tests/conformance/p18/e18_3_parallel]
spec: [spec/SPEC-23-parallel-compilation.md, tasks/0473, tasks/0528, tasks/0530, tasks/0790]
covers: [REQ-LNK-1004, REQ-LNK-1005, REQ-LNK-1006, REQ-LNK-1007, REQ-LNK-1008, REQ-LNK-1009, REQ-LNK-1010, REQ-LNK-1011, REQ-LNK-1012, REQ-LNK-1013, REQ-LNK-1014, REQ-LNK-1015, REQ-LNK-1016, REQ-LNK-1017, REQ-LNK-1018, REQ-LNK-1019, REQ-LNK-1020, REQ-LNK-1021, REQ-LNK-1022, REQ-LNK-1023, REQ-LNK-1024, REQ-LNK-1025, REQ-LNK-1026, REQ-LNK-1027, REQ-LNK-1028, REQ-LNK-1029, REQ-LNK-1030, REQ-LNK-1031, REQ-LNK-1032, REQ-LNK-1033, REQ-LNK-1204, REQ-LNK-1205, REQ-LNK-1206, REQ-LNK-1207, REQ-LNK-1208, REQ-LNK-1209, REQ-LNK-1210, REQ-LNK-1211, REQ-LNK-1212, REQ-LNK-1213, REQ-LNK-1214, REQ-LNK-1215, REQ-LNK-1216, REQ-LNK-1217, REQ-LNK-1218, REQ-LNK-1219, REQ-LNK-1220, REQ-LNK-1221, REQ-LNK-1222, REQ-LNK-1223, REQ-LNK-1224, REQ-LNK-1225, REQ-LNK-1226, REQ-LNK-1227, REQ-LNK-1228, REQ-LNK-1229, REQ-LNK-1230, REQ-LNK-1231, REQ-LNK-1232, REQ-LNK-1233]
started: 2026-11-08 01:47:39
agent: T763-impl
---
# T763 — E18.3 — Parallel compilation thread-count invariance & byte-identical determinism conformance suite

## Goal
Certify E18.3 exit criteria with an end-to-end conformance suite verifying thread-count invariance (`--jobs 1` vs `--jobs 2` vs `--jobs 4` vs `--jobs 8`), cross-worker cycle handling, and byte-identical outputs under parallel compilation.

## Scope
- Create conformance tests in `tests/conformance/p18/e18_3_parallel` verifying:
  - byte-identical `.obj`/`.exe` outputs and identical HIR/MIR/LIR dumps across `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8`;
  - identical multi-file error and warning diagnostic ordering under randomized worker scheduling delays;
  - combined parallel + incremental rebuild determinism;
  - differential equivalence between `--interp` and parallel native builds (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p18/e18_3_parallel` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T763-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T763/build` and `python tools/axtest.py --compiler build-snap-T763/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:15 created by T218 (P18 phase planning)
- 2026-11-08 01:47:39 started (attempt 1) T763-impl
