---
id: T126
title: Slices: sub-ranges and disjoint split
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T048b]
priority: 69
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/own/cap, bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/slice, tests/ui/slice]
locks: [bootstrap/axiom0/src/diag/codes/CAP.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [spec/SPEC-11-capability.md, 0177, 0021, 0028, tasks/0395, tasks/0326, 0087]
covers: []
---
# T126 — Slices: sub-ranges and disjoint split

## Goal
Sub-range views (`s[a..b]`) and their symbolic range disjointness reasoning for borrow checking.

## Scope
- Sub-range views `s[a..b]`, `s[a..]`, `s[..b]` with checked bounds.
- Introduce new MIR projection kind (e.g. `AX_MIR_PROJ_SUB_SLICE`) to represent a sub-slice place.
- Symbolic reasoning in `ax_mir_region_relate` to prove that disjoint sub-ranges like `a..b` and `b..c` are indeed disjoint.
- Disjoint split of a `mut_view` accepted by the region analysis; overlapping mutable sub-views rejected.

## Acceptance
- [ ] Sub-range view tests pass, including out-of-range bounds panics.
- [ ] Borrow checker correctly accepts disjoint split and rejects overlapping mutable sub-views.
- [ ] Full test suite passes.
