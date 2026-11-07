---
id: T761
title: E18.3 — Thread-safe immutable compiler snapshots, sharded interner & work-stealing query scheduler
phase: P18-compiler-architecture-2-0
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T760, T753]
priority: 711
status: todo
attempts: 0
paths: [compiler/parallel/scheduler, tests/run/parallel_scheduler]
spec: [spec/SPEC-23-parallel-compilation.md, tasks/0528, tasks/0530, tasks/0593, tasks/0790]
covers: [REQ-TOOL-224, REQ-TOOL-225, REQ-TOOL-226, REQ-TOOL-227, REQ-TOOL-228, REQ-TOOL-229, REQ-TOOL-230, REQ-TOOL-231, REQ-TOOL-232, REQ-TOOL-233, REQ-TOOL-234, REQ-TOOL-235, REQ-TOOL-236, REQ-TOOL-237, REQ-TOOL-238, REQ-TOOL-239, REQ-TOOL-240, REQ-TOOL-241, REQ-TOOL-242, REQ-TOOL-243, REQ-TOOL-244, REQ-TOOL-245, REQ-TOOL-246, REQ-TOOL-247, REQ-TOOL-248, REQ-TOOL-249, REQ-TOOL-250, REQ-TOOL-251, REQ-TOOL-252, REQ-TOOL-253, REQ-TOOL-254, REQ-LNK-1034, REQ-LNK-1035, REQ-LNK-1036, REQ-LNK-1037, REQ-LNK-1038, REQ-LNK-1039, REQ-LNK-1040, REQ-LNK-1041, REQ-LNK-1042, REQ-LNK-1043, REQ-LNK-1044, REQ-LNK-1045, REQ-LNK-1046, REQ-LNK-1047, REQ-LNK-1048, REQ-LNK-1049, REQ-LNK-1050, REQ-LNK-1051, REQ-LNK-1052, REQ-LNK-1053, REQ-LNK-1054, REQ-LNK-1055, REQ-LNK-1056, REQ-LNK-1057, REQ-LNK-1058, REQ-LNK-1059, REQ-LNK-1060, REQ-LNK-1061, REQ-LNK-1062, REQ-LNK-1063, REQ-LNK-1064, REQ-LNK-1065, REQ-LNK-1066, REQ-LNK-1067, REQ-LNK-1068, REQ-LNK-1069, REQ-LNK-1070, REQ-LNK-1071, REQ-LNK-1072, REQ-LNK-1073, REQ-LNK-1074, REQ-LNK-1075, REQ-LNK-1076, REQ-LNK-1077, REQ-LNK-1078, REQ-LNK-1079, REQ-LNK-1080, REQ-LNK-1081, REQ-LNK-1082, REQ-LNK-1083, REQ-LNK-1084, REQ-LNK-1085, REQ-LNK-1086, REQ-LNK-1087, REQ-LNK-1088, REQ-LNK-1089, REQ-LNK-1090, REQ-LNK-1091, REQ-LNK-1092, REQ-LNK-1093, REQ-LNK-1094, REQ-LNK-1095, REQ-LNK-1096, REQ-LNK-1097, REQ-LNK-1098, REQ-LNK-1099, REQ-LNK-1100, REQ-LNK-1101, REQ-LNK-1102, REQ-LNK-1103, REQ-LNK-1104, REQ-LNK-1105, REQ-LNK-1106, REQ-LNK-1107, REQ-LNK-1108, REQ-LNK-1109, REQ-LNK-1110, REQ-LNK-1111, REQ-LNK-1112, REQ-LNK-1113, REQ-LNK-1114, REQ-LNK-1115, REQ-LNK-1116, REQ-LNK-1117, REQ-LNK-1118, REQ-LNK-1119, REQ-LNK-1120, REQ-LNK-1121, REQ-LNK-1122, REQ-LNK-1123, REQ-LNK-1124, REQ-LNK-1125, REQ-LNK-1126, REQ-LNK-1127, REQ-LNK-1128, REQ-LNK-1129, REQ-LNK-1130, REQ-LNK-1131, REQ-LNK-1132, REQ-LNK-1133]
---
# T761 — E18.3 — Thread-safe immutable compiler snapshots, sharded interner & work-stealing query scheduler

## Goal
Implement thread-safe immutable `CompilerDB` snapshots, sharded content-addressed interning, single-flight query deduplication, and the work-stealing query scheduler (`--jobs N`) in `compiler/parallel/scheduler` per `spec/SPEC-23-parallel-compilation.md`.

## Scope
- Implement sharded, deterministic string/type interning and `(ModuleId, LocalIndex)` semantic IDs in `compiler/parallel/scheduler` so concurrent lexing, parsing, HIR lowering, and typechecking assign identical IDs regardless of thread scheduling (`tasks/0528`, `tasks/0530`).
- Implement single-flight query latches so concurrent workers requesting the same `(QueryKind, Key)` wait for the single computing worker, with wait-for-graph cycle detection across worker threads (`tasks/0790`).
- Implement the work-stealing task pool controlled by `--jobs <N>` (defaulting to logical CPU count, `--jobs 1` deterministic single-thread fallback).

## Acceptance
- [ ] Tests in `tests/run/parallel_scheduler` verify parallel lex/parse/resolve/typeck across multi-module workspaces, cross-worker cycle detection, and identical HIR/MIR dumps under `--jobs 1`, `--jobs 2`, and `--jobs 8`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T761-report.md` with exact `## Files changed`.

## Out of scope
- Parallel backend codegen and object merging (`T762`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T761/build` and `python tools/axtest.py --compiler build-snap-T761/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:15 created by T218 (P18 phase planning)
