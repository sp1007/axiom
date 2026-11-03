---
id: T903
title: E21.1 Collections breadth, SoA layout & generational handle conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T902]
priority: 213
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_1_collections_soa]
spec: [spec/SPEC-120-collections-data-oriented-storage.md, 0210, tasks/0348, tasks/0349, tasks/0608]
covers: [REQ-RT-365, REQ-RT-366, REQ-RT-367, REQ-RT-368, REQ-RT-369, REQ-RT-370, REQ-RT-371, REQ-RT-372, REQ-RT-373, REQ-RT-374, REQ-RT-375, REQ-RT-376, REQ-RT-377, REQ-RT-378, REQ-RT-379, REQ-RT-380, REQ-RT-381, REQ-RT-382, REQ-RT-383, REQ-RT-384, REQ-RT-385, REQ-RT-386, REQ-RT-387, REQ-RT-388, REQ-RT-389, REQ-RT-390, REQ-RT-391, REQ-RT-392, REQ-RT-393, REQ-RT-394]
---
# T903 — E21.1 Collections breadth, SoA layout & generational handle conformance suite

## Goal
Certify E21.1 exit criteria with an end-to-end conformance suite covering `VecDeque`, `BTreeMap`/`BTreeSet`, `BinaryHeap`, `SmallVec`, `SlotMap`/`DenseSlotMap`, `SoA` column projections, and `BitSet`.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_1_collections_soa` verifying deterministic `BTreeMap`/`BTreeSet` range splits and ordered iteration against reference sequences (`0210 §7-10`).
- Verify `SlotMap` and `DenseSlotMap` generational wrap-around safety, stale-key rejection after `remove` + re-insert, and `SecondaryMap` synchronization (`tasks/0349 §10-22`).
- Verify `SoA` disjoint column `view`/`mut_view` borrow legality, cache-aligned column strides, and `Drop` element cleanup on scope exit and `clear` (`tasks/0348 §19-31`).
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_1_collections_soa` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T903-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T903/build` and `python tools/axtest.py --compiler build-snap-T903/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
