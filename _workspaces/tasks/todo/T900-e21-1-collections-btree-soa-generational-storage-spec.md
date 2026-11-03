---
id: T900
title: E21.1 Canonical collections breadth, B-tree, SoA & generational storage specification (SPEC-120)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 210
status: todo
attempts: 0
paths: [spec/SPEC-120-collections-data-oriented-storage.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0210, tasks/0348, tasks/0349, tasks/0608]
covers: [REQ-RT-188, REQ-RT-189, REQ-RT-190, REQ-RT-191, REQ-RT-192, REQ-RT-193, REQ-RT-194, REQ-RT-195, REQ-RT-196, REQ-RT-197, REQ-RT-198, REQ-RT-199, REQ-RT-200, REQ-RT-201, REQ-RT-202, REQ-RT-203, REQ-RT-204, REQ-RT-205, REQ-RT-206, REQ-RT-207, REQ-RT-208, REQ-RT-209, REQ-RT-210, REQ-RT-211, REQ-RT-212, REQ-RT-213, REQ-RT-214, REQ-RT-215, REQ-RT-216, REQ-RT-217, REQ-RT-218, REQ-RT-219, REQ-RT-220, REQ-RT-221, REQ-RT-222, REQ-RT-223, REQ-RT-224, REQ-RT-225, REQ-RT-226, REQ-RT-227, REQ-RT-228, REQ-RT-229, REQ-RT-230, REQ-RT-231, REQ-RT-232, REQ-RT-233, REQ-RT-234, REQ-RT-235, REQ-RT-236, REQ-RT-237, REQ-RT-238, REQ-RT-239, REQ-RT-240, REQ-RT-241, REQ-RT-242, REQ-RT-243, REQ-RT-244, REQ-RT-245, REQ-RT-246, REQ-RT-247, REQ-RT-248, REQ-RT-249, REQ-RT-250]
---
# T900 — E21.1 Canonical collections breadth, B-tree, SoA & generational storage specification (SPEC-120)

## Goal
Consolidate the canonical specification for Axiom's complete collections family, cache-friendly B-tree containers, Structure-of-Arrays (SoA) storage, and generational handle arenas into `spec/SPEC-120-collections-data-oriented-storage.md` (`AXS-COL-*` rule IDs).

## Scope
- Write `spec/SPEC-120-collections-data-oriented-storage.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-COL-NNN` rules.
- Specify contiguous and cache-friendly sequence/ordered containers (`0210 §3-12`, `tasks/0348 §4-18`, `tasks/0608 §2-10`): `VecDeque<T>` ring buffer (`as_slices`, `make_contiguous`), cache-line-tuned `BTreeMap<K, V>` and `BTreeSet<T>` (`Ord`-based range queries, cursor splits, deterministic iteration), `BinaryHeap<T>`, `SmallVec<T, N>`, and `BitSet`.
- Specify address-independent identity and generational storage (`0210 §13-19`, `tasks/0349 §3-22`): `GenKey<T>` `(index: u32, generation: u32)`, `SlotMap<K, V>` with O(1) ABA-safe lookup/removal, `SecondaryMap<K, V>` sparse/dense attachments, and deterministic stale-handle rejection (`Option.None` vs trap policy).
- Specify Structure-of-Arrays (`SoA`) multi-column containers (`tasks/0348 §19-31`, `tasks/0608 §11-16`): aligned column buffers, disjoint column `view<ColA>` / `mut_view<ColB>` projections for SIMD/cache-friendly iteration, and capability invalidation rules across structural mutation (`push`, `swap_remove`, `reserve`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-120-collections-data-oriented-storage.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-COL-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T900-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of collection containers and SoA/handle tables (`T901`–`T902`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T900/build` and `python tools/axtest.py --compiler build-snap-T900/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
