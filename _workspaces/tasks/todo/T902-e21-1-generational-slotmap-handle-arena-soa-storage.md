---
id: T902
title: E21.1 Generational SlotMap, dense HandleArena & Structure-of-Arrays (SoA) storage
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T900, T901]
priority: 212
status: todo
attempts: 0
paths: [std/collections/slot_map, std/collections/soa, std/collections/bit_set, tests/run/std_soa_handles]
spec: [spec/SPEC-120-collections-data-oriented-storage.md, 0210, tasks/0348, tasks/0349, tasks/0608]
covers: [REQ-RT-315, REQ-RT-316, REQ-RT-317, REQ-RT-318, REQ-RT-319, REQ-RT-320, REQ-RT-321, REQ-RT-322, REQ-RT-323, REQ-RT-324, REQ-RT-325, REQ-RT-326, REQ-RT-327, REQ-RT-328, REQ-RT-329, REQ-RT-330, REQ-RT-331, REQ-RT-332, REQ-RT-333, REQ-RT-334, REQ-RT-335, REQ-RT-336, REQ-RT-337, REQ-RT-338, REQ-RT-339, REQ-RT-340, REQ-RT-341, REQ-RT-342, REQ-RT-343, REQ-RT-344, REQ-RT-345, REQ-RT-346, REQ-RT-347, REQ-RT-348, REQ-RT-349, REQ-RT-350, REQ-RT-351, REQ-RT-352, REQ-RT-353, REQ-RT-354, REQ-RT-355, REQ-RT-356, REQ-RT-357, REQ-RT-358, REQ-RT-359, REQ-RT-360, REQ-RT-361, REQ-RT-362, REQ-RT-363, REQ-RT-364]
---
# T902 — E21.1 Generational SlotMap, dense HandleArena & Structure-of-Arrays (SoA) storage

## Goal
Implement generational handle maps (`SlotMap<K, V>`, `DenseSlotMap<K, V>`, `SecondaryMap<K, V>`), `BitSet`, and Structure-of-Arrays (`SoA`) multi-column containers in `std.collections` per `spec/SPEC-120-collections-data-oriented-storage.md`.

## Scope
- Implement `std/collections/slot_map` (`GenKey`, `SlotMap<K, V>`, `DenseSlotMap<K, V>`, `SecondaryMap<K, V>` with 32-bit index + 32-bit generation counters, ABA-safe slot reuse, O(1) dense removal via swap-and-relink, and stale-handle detection; `tasks/0349 §5-20`).
- Implement `std/collections/soa` (`SoaTable2`/`SoaTable3`/`SoaTable4` and column-slice descriptors with cache-line-aligned column buffers, disjoint column `view`/`mut_view` splitting for simultaneous read/write column kernels, and `swap_remove`; `tasks/0348 §19-30`, `tasks/0608 §11-15`).
- Implement `std/collections/bit_set` (`BitSet` and `BitVec` with `set`, `clear`, `test`, `union_with`, `intersect_with`, `ones()` iterator via hardware `ctz`).
- Add run tests in `tests/run/std_soa_handles`.

## Acceptance
- [ ] Run tests in `tests/run/std_soa_handles` verify `SlotMap` generational ABA rejection, `DenseSlotMap` contiguous iteration, `SecondaryMap` sparse association, disjoint `SoA` column views, and `BitSet` set operations in both `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T902-report.md` with exact `## Files changed`.

## Out of scope
- Unicode text normalization (`E21.2`) and custom slab/pool allocators (`E21.9`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T902/build` and `python tools/axtest.py --compiler build-snap-T902/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
