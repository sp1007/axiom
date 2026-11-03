---
id: T757
title: E18.2 — Fine-grained AST/API/body/codegen fingerprints & red-green change propagation
phase: P18-compiler-architecture-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T756, T754]
priority: 707
status: todo
attempts: 0
paths: [compiler/incremental/fingerprint, tests/run/incremental_fingerprint]
spec: [spec/SPEC-22-incremental-compilation.md, 0142, 0152, tasks/0564, tasks/0778, tasks/0792]
covers: [REQ-LNK-1514, REQ-LNK-1515, REQ-LNK-1516, REQ-LNK-1517, REQ-LNK-1518, REQ-LNK-1519, REQ-LNK-1520, REQ-LNK-1521, REQ-LNK-1522, REQ-LNK-1523, REQ-LNK-1524, REQ-LNK-1525, REQ-LNK-1526, REQ-LNK-1527, REQ-LNK-1528, REQ-LNK-1529, REQ-LNK-1530, REQ-LNK-1531, REQ-LNK-1532, REQ-LNK-1533, REQ-LNK-1534, REQ-LNK-1535, REQ-LNK-1536, REQ-LNK-1537, REQ-LNK-1538, REQ-LNK-1539, REQ-LNK-1540, REQ-LNK-1541, REQ-LNK-1542, REQ-LNK-1543, REQ-LNK-1544, REQ-LNK-1545, REQ-LNK-1546, REQ-LNK-1547, REQ-LNK-1548, REQ-LNK-1549, REQ-LNK-1550, REQ-LNK-1551, REQ-LNK-1552, REQ-LNK-1553, REQ-LNK-1554, REQ-LNK-1555, REQ-LNK-1556, REQ-LNK-1557, REQ-LNK-1558, REQ-LNK-1559, REQ-LNK-1560, REQ-LNK-1561, REQ-LNK-1562, REQ-LNK-1563, REQ-LNK-1564, REQ-LNK-1565, REQ-LNK-1566, REQ-LNK-1567, REQ-LNK-1568, REQ-LNK-1569, REQ-LNK-1570, REQ-LNK-1571, REQ-LNK-1572, REQ-LNK-1573, REQ-LNK-1574, REQ-LNK-1575, REQ-LNK-1576, REQ-LNK-1577, REQ-LNK-1578, REQ-LNK-1579, REQ-LNK-1580, REQ-LNK-1581, REQ-LNK-1582, REQ-LNK-1583, REQ-LNK-1584, REQ-LNK-1585, REQ-LNK-1586, REQ-LNK-1587, REQ-LNK-1588, REQ-LNK-1589, REQ-LNK-1590, REQ-LNK-1591, REQ-LNK-1592, REQ-LNK-1593, REQ-LNK-1594, REQ-LNK-1595, REQ-LNK-1596, REQ-LNK-1597, REQ-LNK-1598, REQ-LNK-1599, REQ-LNK-1600, REQ-LNK-1601, REQ-LNK-1602, REQ-LNK-1603]
---
# T757 — E18.2 — Fine-grained AST/API/body/codegen fingerprints & red-green change propagation

## Goal
Implement deterministic 128-bit structural, API, semantic, and codegen fingerprints (`0152 §78`) plus red-green change propagation in `compiler/incremental/fingerprint` per `spec/SPEC-22-incremental-compilation.md`.

## Scope
- Implement canonical hashing in `compiler/incremental/fingerprint` for source files, comment/whitespace-insensitive AST items, exported module/item signatures (`InterfaceFingerprint`), Verified MIR bodies (`BodyFingerprint`), and monomorphized codegen units (`CodegenFingerprint`).
- Implement red-green `try_mark_green` dependency verification over `CompilerDB` so queries whose inputs' fingerprints remain unchanged are marked green without re-executing downstream typeck/MIR passes (`tasks/0778`, `tasks/0792`).
- Track cross-module `const` evaluation, generic instantiations, and inlined body dependencies in `CodegenFingerprint` so changing an inlined or `const` body invalidates only affected callers.
- Add `inspect --emit=fingerprints` and `--emit=incremental-stats` to report per-item fingerprints and re-evaluated vs reused queries.

## Acceptance
- [ ] Tests in `tests/run/incremental_fingerprint` verify that whitespace/comment edits preserve AST/API/body fingerprints, editing a private non-inlined function body re-typechecks only that module (`0` downstream `typeck` queries re-run), and signature edits propagate strictly to dependent items.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T757-report.md` with exact `## Files changed`.

## Out of scope
- Persistent on-disk cache serialization and fast no-op rebuild driver (`T758`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T757/build` and `python tools/axtest.py --compiler build-snap-T757/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:57:30 created by T218 (P18 phase planning)
