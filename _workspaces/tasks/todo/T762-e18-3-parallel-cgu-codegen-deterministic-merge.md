---
id: T762
title: E18.3 — Parallel per-module/per-CGU codegen & deterministic diagnostic/artifact merging
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T761]
priority: 712
status: todo
attempts: 0
paths: [compiler/parallel/codegen, tests/run/parallel_codegen]
spec: [spec/SPEC-23-parallel-compilation.md, tasks/0473, tasks/0528, tasks/0530, tasks/0789, tasks/0790]
covers: [REQ-LNK-934, REQ-LNK-935, REQ-LNK-936, REQ-LNK-937, REQ-LNK-938, REQ-LNK-939, REQ-LNK-940, REQ-LNK-941, REQ-LNK-942, REQ-LNK-943, REQ-LNK-944, REQ-LNK-945, REQ-LNK-946, REQ-LNK-947, REQ-LNK-948, REQ-LNK-949, REQ-LNK-950, REQ-LNK-951, REQ-LNK-952, REQ-LNK-953, REQ-LNK-954, REQ-LNK-955, REQ-LNK-956, REQ-LNK-957, REQ-LNK-958, REQ-LNK-959, REQ-LNK-960, REQ-LNK-961, REQ-LNK-962, REQ-LNK-963, REQ-LNK-964, REQ-LNK-965, REQ-LNK-966, REQ-LNK-967, REQ-LNK-968, REQ-LNK-969, REQ-LNK-970, REQ-LNK-971, REQ-LNK-972, REQ-LNK-973, REQ-LNK-974, REQ-LNK-975, REQ-LNK-976, REQ-LNK-977, REQ-LNK-978, REQ-LNK-979, REQ-LNK-980, REQ-LNK-981, REQ-LNK-982, REQ-LNK-983, REQ-LNK-984, REQ-LNK-985, REQ-LNK-986, REQ-LNK-987, REQ-LNK-988, REQ-LNK-989, REQ-LNK-990, REQ-LNK-991, REQ-LNK-992, REQ-LNK-993, REQ-LNK-994, REQ-LNK-995, REQ-LNK-996, REQ-LNK-997, REQ-LNK-998, REQ-LNK-999, REQ-LNK-1000, REQ-LNK-1001, REQ-LNK-1002, REQ-LNK-1003, REQ-LNK-1134, REQ-LNK-1135, REQ-LNK-1136, REQ-LNK-1137, REQ-LNK-1138, REQ-LNK-1139, REQ-LNK-1140, REQ-LNK-1141, REQ-LNK-1142, REQ-LNK-1143, REQ-LNK-1144, REQ-LNK-1145, REQ-LNK-1146, REQ-LNK-1147, REQ-LNK-1148, REQ-LNK-1149, REQ-LNK-1150, REQ-LNK-1151, REQ-LNK-1152, REQ-LNK-1153, REQ-LNK-1154, REQ-LNK-1155, REQ-LNK-1156, REQ-LNK-1157, REQ-LNK-1158, REQ-LNK-1159, REQ-LNK-1160, REQ-LNK-1161, REQ-LNK-1162, REQ-LNK-1163, REQ-LNK-1164, REQ-LNK-1165, REQ-LNK-1166, REQ-LNK-1167, REQ-LNK-1168, REQ-LNK-1169, REQ-LNK-1170, REQ-LNK-1171, REQ-LNK-1172, REQ-LNK-1173, REQ-LNK-1174, REQ-LNK-1175, REQ-LNK-1176, REQ-LNK-1177, REQ-LNK-1178, REQ-LNK-1179, REQ-LNK-1180, REQ-LNK-1181, REQ-LNK-1182, REQ-LNK-1183, REQ-LNK-1184, REQ-LNK-1185, REQ-LNK-1186, REQ-LNK-1187, REQ-LNK-1188, REQ-LNK-1189, REQ-LNK-1190, REQ-LNK-1191, REQ-LNK-1192, REQ-LNK-1193, REQ-LNK-1194, REQ-LNK-1195, REQ-LNK-1196, REQ-LNK-1197, REQ-LNK-1198, REQ-LNK-1199, REQ-LNK-1200, REQ-LNK-1201, REQ-LNK-1202, REQ-LNK-1203]
---
# T762 — E18.3 — Parallel per-module/per-CGU codegen & deterministic diagnostic/artifact merging

## Goal
Implement parallel per-module and per-codegen-unit (`CGU`) LIR lowering, machine encoding, and object emission with canonical order-independent diagnostic and artifact merging in `compiler/parallel/codegen` per `spec/SPEC-23-parallel-compilation.md`.

## Scope
- Partition Verified MIR / `OptIR` into deterministic codegen units (`CGU`s) in `compiler/parallel/codegen` and execute LIR lowering, register allocation, machine encoding, and COFF `.obj` emission in parallel across worker threads (`tasks/0790`).
- Merge per-worker diagnostic buffers in canonical `(file_id, byte_offset, code, message)` order and feed per-CGU `.obj` buffers to the linker in canonical CGU index order (`tasks/0473`, `tasks/0528`).
- Integrate parallel CGU execution with the incremental cache (`T758`) so unchanged CGUs are loaded from cache while dirty CGUs compile in parallel (`tasks/0789`).

## Acceptance
- [ ] Tests in `tests/run/parallel_codegen` verify that `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8` produce byte-identical `.obj` and `.exe` binaries and identical diagnostic streams.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T762-report.md` with exact `## Files changed`.

## Out of scope
- Separate-compilation archive/section-GC linker enhancements (`E18.6` `T067`, `T774`–`T776`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T762/build` and `python tools/axtest.py --compiler build-snap-T762/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:15 created by T218 (P18 phase planning)
