---
id: T901
title: E21.1 VecDeque, BTreeMap, BTreeSet, BinaryHeap & SmallVec collections
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T900]
priority: 211
status: todo
attempts: 0
paths: [std/collections/deque, std/collections/btree, std/collections/heap, std/collections/small_vec, tests/run/std_collections]
spec: [spec/SPEC-120-collections-data-oriented-storage.md, 0210, tasks/0348, tasks/0608]
covers: [REQ-RT-251, REQ-RT-252, REQ-RT-253, REQ-RT-254, REQ-RT-255, REQ-RT-256, REQ-RT-257, REQ-RT-258, REQ-RT-259, REQ-RT-260, REQ-RT-261, REQ-RT-262, REQ-RT-263, REQ-RT-264, REQ-RT-265, REQ-RT-266, REQ-RT-267, REQ-RT-268, REQ-RT-269, REQ-RT-270, REQ-RT-271, REQ-RT-272, REQ-RT-273, REQ-RT-274, REQ-RT-275, REQ-RT-276, REQ-RT-277, REQ-RT-278, REQ-RT-279, REQ-RT-280, REQ-RT-281, REQ-RT-282, REQ-RT-283, REQ-RT-284, REQ-RT-285, REQ-RT-286, REQ-RT-287, REQ-RT-288, REQ-RT-289, REQ-RT-290, REQ-RT-291, REQ-RT-292, REQ-RT-293, REQ-RT-294, REQ-RT-295, REQ-RT-296, REQ-RT-297, REQ-RT-298, REQ-RT-299, REQ-RT-300, REQ-RT-301, REQ-RT-302, REQ-RT-303, REQ-RT-304, REQ-RT-305, REQ-RT-306, REQ-RT-307, REQ-RT-308, REQ-RT-309, REQ-RT-310, REQ-RT-311, REQ-RT-312, REQ-RT-313, REQ-RT-314]
---
# T901 — E21.1 VecDeque, BTreeMap, BTreeSet, BinaryHeap & SmallVec collections

## Goal
Implement `VecDeque<T>`, `BTreeMap<K, V>`, `BTreeSet<T>`, `BinaryHeap<T>`, and `SmallVec<T, N>` in `std.collections` per `spec/SPEC-120-collections-data-oriented-storage.md`.

## Scope
- Implement `std/collections/deque` (`VecDeque<T>`: `push_front`, `push_back`, `pop_front`, `pop_back`, `as_slices`, `make_contiguous`, `rotate_left`, `rotate_right`, and `Drop` element cleanup; `0210 §4-6`, `tasks/0348 §8`).
- Implement `std/collections/btree` (`BTreeMap<K, V>` and `BTreeSet<T>` with cache-friendly B-tree nodes, `insert`, `get`, `get_mut`, `remove`, `range`, `first_key_value`, `last_key_value`, `split_off`, and `Entry` API; `0210 §7-10`, `tasks/0608 §6-8`).
- Implement `std/collections/heap` (`BinaryHeap<T>` max/min-heap with `push`, `pop`, `peek`, `into_sorted_vec`) and `std/collections/small_vec` (`SmallVec<T, N>` inline-to-heap transition preserving ownership and `Drop`).
- Add comprehensive run tests in `tests/run/std_collections`.

## Acceptance
- [ ] Run tests in `tests/run/std_collections` verify `VecDeque`, `BTreeMap`, `BTreeSet`, `BinaryHeap`, and `SmallVec` ordering, range queries, reallocation invariants, and `Drop` cleanup in both `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T901-report.md` with exact `## Files changed`.

## Out of scope
- Generational `SlotMap` and `SoA` multi-column storage (`T902`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T901/build` and `python tools/axtest.py --compiler build-snap-T901/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
