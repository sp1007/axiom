---
id: T754
title: E18.1 — Deterministic query cycle detection, snapshot-bound diagnostics & invalidation
phase: P18-compiler-architecture-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T753]
priority: 704
status: todo
attempts: 0
paths: [compiler/query/engine, tests/run/query_cycles, tests/selfhost]
spec: [spec/SPEC-21-query-engine-semantic-db.md, tasks/0384, tasks/0530, tasks/0533, tasks/0781, tasks/0791]
covers: [REQ-TOOL-192, REQ-TOOL-193, REQ-TOOL-194, REQ-TOOL-195, REQ-TOOL-196, REQ-TOOL-197, REQ-TOOL-198, REQ-TOOL-199, REQ-TOOL-200, REQ-TOOL-201, REQ-TOOL-202, REQ-TOOL-203, REQ-TOOL-204, REQ-TOOL-205, REQ-TOOL-206, REQ-TOOL-207, REQ-TOOL-208, REQ-TOOL-209, REQ-TOOL-210, REQ-TOOL-211, REQ-TOOL-212, REQ-TOOL-213, REQ-TOOL-214, REQ-TOOL-215, REQ-TOOL-216, REQ-TOOL-217, REQ-TOOL-218, REQ-TOOL-219, REQ-TOOL-220, REQ-TOOL-221, REQ-TOOL-222, REQ-TOOL-223, REQ-LNK-1234, REQ-LNK-1235, REQ-LNK-1236, REQ-LNK-1237, REQ-LNK-1238, REQ-LNK-1239, REQ-LNK-1240, REQ-LNK-1241, REQ-LNK-1242, REQ-LNK-1243, REQ-LNK-1244, REQ-LNK-1245, REQ-LNK-1246, REQ-LNK-1247, REQ-LNK-1248, REQ-LNK-1249, REQ-LNK-1250, REQ-LNK-1251, REQ-LNK-1252, REQ-LNK-1253, REQ-LNK-1254, REQ-LNK-1255, REQ-LNK-1256, REQ-LNK-1257, REQ-LNK-1258, REQ-LNK-1259, REQ-LNK-1260, REQ-LNK-1261, REQ-LNK-1262, REQ-LNK-1263, REQ-LNK-1264, REQ-LNK-1265, REQ-LNK-1266, REQ-LNK-1267, REQ-LNK-1268, REQ-LNK-1269, REQ-LNK-1270, REQ-LNK-1271, REQ-LNK-1272, REQ-LNK-1273, REQ-LNK-1274, REQ-LNK-1275, REQ-LNK-1276, REQ-LNK-1277, REQ-LNK-1278, REQ-LNK-1279, REQ-LNK-1280, REQ-LNK-1281, REQ-LNK-1282, REQ-LNK-1283, REQ-LNK-1284, REQ-LNK-1285, REQ-LNK-1286, REQ-LNK-1287, REQ-LNK-1288, REQ-LNK-1289, REQ-LNK-1290, REQ-LNK-1291, REQ-LNK-1292, REQ-LNK-1293, REQ-LNK-1294, REQ-LNK-1295, REQ-LNK-1296, REQ-LNK-1297, REQ-LNK-1298, REQ-LNK-1299, REQ-LNK-1300, REQ-LNK-1301, REQ-LNK-1302, REQ-LNK-1303, REQ-LNK-1304, REQ-LNK-1305, REQ-LNK-1306, REQ-LNK-1307, REQ-LNK-1308, REQ-LNK-1309, REQ-LNK-1310, REQ-LNK-1311, REQ-LNK-1312, REQ-LNK-1313, REQ-LNK-1314, REQ-LNK-1315, REQ-LNK-1316, REQ-LNK-1317, REQ-LNK-1318, REQ-LNK-1319, REQ-LNK-1320, REQ-LNK-1321, REQ-LNK-1322, REQ-LNK-1323, REQ-LNK-1324, REQ-LNK-1325, REQ-LNK-1326, REQ-LNK-1327, REQ-LNK-1328, REQ-LNK-1329, REQ-LNK-1330, REQ-LNK-1331, REQ-LNK-1332, REQ-LNK-1333, REQ-LNK-1334, REQ-LNK-1335, REQ-LNK-1336, REQ-LNK-1337, REQ-LNK-1338, REQ-LNK-1339, REQ-LNK-1340, REQ-LNK-1341, REQ-LNK-1342, REQ-LNK-1343, REQ-LNK-1344, REQ-LNK-1345, REQ-LNK-1346, REQ-LNK-1347, REQ-LNK-1348, REQ-LNK-1349, REQ-LNK-1350, REQ-LNK-1351, REQ-LNK-1352, REQ-LNK-1353, REQ-LNK-1354, REQ-LNK-1355, REQ-LNK-1356, REQ-LNK-1357, REQ-LNK-1358, REQ-LNK-1359, REQ-LNK-1360, REQ-LNK-1361, REQ-LNK-1362, REQ-LNK-1363, REQ-LNK-1364, REQ-LNK-1365, REQ-LNK-1366, REQ-LNK-1367, REQ-LNK-1368, REQ-LNK-1369, REQ-LNK-1370, REQ-LNK-1371, REQ-LNK-1372, REQ-LNK-1373, REQ-LNK-1374, REQ-LNK-1375, REQ-LNK-1376, REQ-LNK-1377, REQ-LNK-1378, REQ-LNK-1379, REQ-LNK-1380, REQ-LNK-1381, REQ-LNK-1382, REQ-LNK-1383]
---
# T754 — E18.1 — Deterministic query cycle detection, snapshot-bound diagnostics & invalidation

## Goal
Implement deterministic query cycle detection and recovery, snapshot-bound diagnostic accumulation, and revision-based query invalidation in `compiler/query/engine` per `spec/SPEC-21-query-engine-semantic-db.md`.

## Scope
- Implement Tarjan/stack-based cycle detection on the active query stack in `compiler/query/engine`, canonicalizing cycle rotation from the minimum semantic key so cycle diagnostics are independent of entry query order (`tasks/0530`, `tasks/0781`).
- Implement cycle recovery fallback values (`ErrorType`, poisoned const/trait facts) and cascading-error suppression so independent regions continue analysis cleanly (`tasks/0791`).
- Bind emitted diagnostics to the query revision and `CompilerDB` snapshot that produced them, replaying cached diagnostics deterministically on memoized hits.
- Implement input-revision invalidation and transitive dirty marking across the recorded dependency DAG.

## Acceptance
- [ ] Positive and negative tests in `tests/run/query_cycles` verify deterministic cycle diagnostics (recursive type aliases, mutually recursive `const` items, trait obligations), cascading error suppression, and snapshot-bound diagnostic replay.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T754-report.md` with exact `## Files changed`.

## Out of scope
- Persistent on-disk incremental cache and fingerprint comparison (`E18.2` `T756`–`T759`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T754/build` and `python tools/axtest.py --compiler build-snap-T754/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:56:00 created by T218 (P18 phase planning)
