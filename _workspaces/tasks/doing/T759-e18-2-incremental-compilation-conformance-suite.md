---
id: T759
title: E18.2 — Incremental compilation, edit-one-private-fn & <100ms no-op rebuild conformance suite
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T758]
priority: 709
status: doing
attempts: 1
paths: [tests/conformance/p18/e18_2_incremental]
spec: [spec/SPEC-22-incremental-compilation.md, 0142, 0152, tasks/0778, tasks/0788, tasks/0792]
covers: [REQ-LNK-804, REQ-LNK-805, REQ-LNK-806, REQ-LNK-807, REQ-LNK-808, REQ-LNK-809, REQ-LNK-810, REQ-LNK-811, REQ-LNK-812, REQ-LNK-813, REQ-LNK-814, REQ-LNK-815, REQ-LNK-816, REQ-LNK-817, REQ-LNK-818, REQ-LNK-819, REQ-LNK-820, REQ-LNK-821, REQ-LNK-822, REQ-LNK-823, REQ-LNK-824, REQ-LNK-825, REQ-LNK-826, REQ-LNK-827, REQ-LNK-828, REQ-LNK-829, REQ-LNK-830, REQ-LNK-831, REQ-LNK-832, REQ-LNK-833, REQ-LNK-1604, REQ-LNK-1605, REQ-LNK-1606, REQ-LNK-1607, REQ-LNK-1608, REQ-LNK-1609, REQ-LNK-1610, REQ-LNK-1611, REQ-LNK-1612, REQ-LNK-1613, REQ-LNK-1614, REQ-LNK-1615, REQ-LNK-1616, REQ-LNK-1617, REQ-LNK-1618, REQ-LNK-1619, REQ-LNK-1620, REQ-LNK-1621, REQ-LNK-1622, REQ-LNK-1623, REQ-LNK-1624, REQ-LNK-1625, REQ-LNK-1626, REQ-LNK-1627, REQ-LNK-1628, REQ-LNK-1629, REQ-LNK-1630, REQ-LNK-1631, REQ-LNK-1632, REQ-LNK-1633]
started: 2026-11-08 00:30:40
agent: T759-impl
---
# T759 — E18.2 — Incremental compilation, edit-one-private-fn & <100ms no-op rebuild conformance suite

## Goal
Certify E18.2 and the P18 incremental exit criteria (`no-op rebuild < 100 ms on the compiler itself; edit-one-private-fn rebuild re-typechecks only that module`) with an end-to-end conformance suite.

## Scope
- Create conformance tests in `tests/conformance/p18/e18_2_incremental` verifying:
  - no-op rebuild of `axiomc` completes in `< 100 ms` with zero re-executed semantic/codegen queries;
  - editing a private function body in one module re-typechecks only that module (`--emit=incremental-stats` confirms `0` downstream modules re-typechecked);
  - editing a public signature, `const`, or generic body re-evaluates only affected dependents and produces a byte-identical binary to a clean rebuild;
  - differential equivalence between `--interp`, clean native, and incremental native builds (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p18/e18_2_incremental` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T759-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T759/build` and `python tools/axtest.py --compiler build-snap-T759/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:57:30 created by T218 (P18 phase planning)
- 2026-11-08 00:30:40 started (attempt 1) T759-impl
