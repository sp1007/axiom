---
id: T756
title: E18.2 — Canonical incremental compilation & fingerprinting specification (SPEC-22)
phase: P18-compiler-architecture-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T752]
priority: 706
status: todo
attempts: 0
paths: [spec/SPEC-22-incremental-compilation.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-21-query-engine-semantic-db.md, 0142, 0152, tasks/0564, tasks/0778, tasks/0788, tasks/0792]
covers: [REQ-CORE-3089, REQ-CORE-3090, REQ-LNK-634, REQ-LNK-635, REQ-LNK-636, REQ-LNK-637, REQ-LNK-638, REQ-LNK-639, REQ-LNK-640, REQ-LNK-641, REQ-LNK-642, REQ-LNK-643, REQ-LNK-644, REQ-LNK-645, REQ-LNK-646, REQ-LNK-647, REQ-LNK-648, REQ-LNK-649, REQ-LNK-650, REQ-LNK-651, REQ-LNK-652, REQ-LNK-653, REQ-LNK-654, REQ-LNK-655, REQ-LNK-656, REQ-LNK-657, REQ-LNK-658, REQ-LNK-659, REQ-LNK-660, REQ-LNK-661, REQ-LNK-662, REQ-LNK-663, REQ-LNK-664, REQ-LNK-665, REQ-LNK-666, REQ-LNK-667, REQ-LNK-668, REQ-LNK-669, REQ-LNK-670, REQ-LNK-671, REQ-LNK-672, REQ-LNK-673, REQ-LNK-674, REQ-LNK-675, REQ-LNK-676, REQ-LNK-677, REQ-LNK-678, REQ-LNK-679, REQ-LNK-680, REQ-LNK-681, REQ-LNK-682, REQ-LNK-683, REQ-LNK-684, REQ-LNK-685, REQ-LNK-686, REQ-LNK-687, REQ-LNK-688, REQ-LNK-689, REQ-LNK-690, REQ-LNK-691, REQ-LNK-692, REQ-LNK-693, REQ-LNK-694, REQ-LNK-695, REQ-LNK-696, REQ-LNK-697, REQ-LNK-698, REQ-LNK-699, REQ-LNK-700, REQ-LNK-701, REQ-LNK-702, REQ-LNK-703, REQ-LNK-704, REQ-LNK-705, REQ-LNK-706, REQ-LNK-707, REQ-LNK-708, REQ-LNK-709, REQ-LNK-710, REQ-LNK-711, REQ-LNK-712, REQ-LNK-713, REQ-LNK-1434, REQ-LNK-1435, REQ-LNK-1436, REQ-LNK-1437, REQ-LNK-1438, REQ-LNK-1439, REQ-LNK-1440, REQ-LNK-1441, REQ-LNK-1442, REQ-LNK-1443, REQ-LNK-1444, REQ-LNK-1445, REQ-LNK-1446, REQ-LNK-1447, REQ-LNK-1448, REQ-LNK-1449, REQ-LNK-1450, REQ-LNK-1451, REQ-LNK-1452, REQ-LNK-1453, REQ-LNK-1454, REQ-LNK-1455, REQ-LNK-1456, REQ-LNK-1457, REQ-LNK-1458, REQ-LNK-1459, REQ-LNK-1460, REQ-LNK-1461, REQ-LNK-1462, REQ-LNK-1463, REQ-LNK-1464, REQ-LNK-1465, REQ-LNK-1466, REQ-LNK-1467, REQ-LNK-1468, REQ-LNK-1469, REQ-LNK-1470, REQ-LNK-1471, REQ-LNK-1472, REQ-LNK-1473, REQ-LNK-1474, REQ-LNK-1475, REQ-LNK-1476, REQ-LNK-1477, REQ-LNK-1478, REQ-LNK-1479, REQ-LNK-1480, REQ-LNK-1481, REQ-LNK-1482, REQ-LNK-1483, REQ-LNK-1484, REQ-LNK-1485, REQ-LNK-1486, REQ-LNK-1487, REQ-LNK-1488, REQ-LNK-1489, REQ-LNK-1490, REQ-LNK-1491, REQ-LNK-1492, REQ-LNK-1493, REQ-LNK-1494, REQ-LNK-1495, REQ-LNK-1496, REQ-LNK-1497, REQ-LNK-1498, REQ-LNK-1499, REQ-LNK-1500, REQ-LNK-1501, REQ-LNK-1502, REQ-LNK-1503, REQ-LNK-1504, REQ-LNK-1505, REQ-LNK-1506, REQ-LNK-1507, REQ-LNK-1508, REQ-LNK-1509, REQ-LNK-1510, REQ-LNK-1511, REQ-LNK-1512, REQ-LNK-1513]
---
# T756 — E18.2 — Canonical incremental compilation & fingerprinting specification (SPEC-22)

## Goal
Consolidate the canonical specification for Axiom's incremental compilation model, structural/API/semantic/codegen fingerprints (`0152 §78`), red-green change propagation, and persistent cache invariants into `spec/SPEC-22-incremental-compilation.md` (`AXS-INC-*` rule IDs).

## Scope
- Write `spec/SPEC-22-incremental-compilation.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-INC-NNN` rules.
- Specify the four-tier fingerprint hierarchy (`0152 §78`, `0142`, `tasks/0778`, `tasks/0792`): source content hash, span-insensitive AST hash, exported module/item API fingerprint (`InterfaceFingerprint`), and function-body / MIR / codegen fingerprint (`BodyFingerprint`, `CodegenFingerprint`).
- Specify the red-green try-mark-green algorithm: editing a non-inlined private function body keeps the module `InterfaceFingerprint` green so downstream modules are never re-typechecked.
- Specify the on-disk incremental cache schema (`tasks/0788`), compiler version/flag/target key binding, atomic corruption-safe writes, and the hard invariant that incremental builds are byte-identical in semantics and diagnostics to clean builds.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-22-incremental-compilation.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-INC-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T756-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of fingerprinting and on-disk caching (`T757`–`T758`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:57:30 created by T218 (P18 phase planning)
