---
id: T572
title: E14.5 — Index auto-deref through view/mut_view conformance suite (AXS-SEM-047)
phase: P14-comptime-2-0-reflection-genera
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T571]
priority: 193
status: todo
attempts: 0
paths: [tests/conformance/p14/e14_5_index_autoderef]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-12-drop.md, spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md]
covers: [REQ-CORE-3059, REQ-CORE-3060]
---
# T572 — E14.5 — Index auto-deref through view/mut_view conformance suite (AXS-SEM-047)

## Goal
Certify E14.5 exit criteria with a comprehensive conformance suite for `SPEC-03 AXS-SEM-047` index auto-deref through `view<[N]T>` and `mut_view<[N]T>` across read, write, compound assignment, `Drop`, evaluation order, and negative raw-pointer/immutability boundaries.

## Scope
- Create positive and negative conformance tests in `tests/conformance/p14/e14_5_index_autoderef` covering:
  - reading `a[i]` on `view<[N]T>`, `mut_view<[N]T>`, and nested views (`view<view<[N]T>>`), plus multidimensional `a[i][j]`;
  - writing `a[i] = v` and `a[i] op= v` on `mut_view<[N]T]`, verifying RHS-before-place evaluation order (`AXS-SEM-043/044`) and deterministic `Drop` of replaced elements (`AXS-DROP-007`);
  - negative UI tests for writing through `view<[N]T>` (or `mut_view<view<[N]T>>`) and indexing a raw pointer `p[i]` (`*const [N]T`, `*mut [N]T`, `*mut T`).

## Acceptance
- [ ] All positive and negative tests in `tests/conformance/p14/e14_5_index_autoderef` pass in both `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T572-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`), epic `E14.5` (`ADR-0036` §4).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T572/build` and `python tools/axtest.py --compiler build-snap-T572/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:24:30 created by T214 (P14 phase planning)
