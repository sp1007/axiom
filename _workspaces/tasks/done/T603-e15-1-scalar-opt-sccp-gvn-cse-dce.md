---
id: T603
title: E15.1 — Unified scalar optimization engine (SCCP, GVN, CSE, DCE & algebraic simplification)
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T602]
priority: 96
status: done
attempts: 1
paths: [compiler/opt/scalar, tests/run/opt_scalar]
spec: [spec/SPEC-70-optir-ssa-memoryssa.md, 0161, 0162, 0165, tasks/0366, tasks/0456, tasks/0465, tasks/0467, tasks/0547]
covers: [REQ-OPT-011, REQ-OPT-014, REQ-OPT-304, REQ-OPT-305, REQ-OPT-306, REQ-OPT-339, REQ-OPT-351, REQ-OPT-352, REQ-OPT-353, REQ-OPT-363, REQ-OPT-364]
started: 2026-11-04 09:02:29
finished: 2026-11-04 16:58:37
---
# T603 — E15.1 — Unified scalar optimization engine (SCCP, GVN, CSE, DCE & algebraic simplification)

## Goal
Implement the unified `OptIR` scalar optimization engine (sparse conditional constant propagation, global value numbering, common subexpression elimination, dead-code/dead-branch elimination, and overflow-aware algebraic simplification) in `compiler/opt/scalar` per `spec/SPEC-70-optir-ssa-memoryssa.md`.

## Scope
- Implement Sparse Conditional Constant Propagation (SCCP) and CFG unreachable-edge pruning in `compiler/opt/scalar`.
- Implement Global Value Numbering (GVN), Common Subexpression Elimination (CSE), and overflow-faithful algebraic identities (distinguishing checked arithmetic traps from `wrapping_*` intrinsics, `0165 §8-9`, `REQ-OPT-014`, `REQ-OPT-363`, `REQ-OPT-364`).
- Implement effect-aware Dead Code Elimination (DCE) that elides dead pure computations and unobservable move/copy temporaries (`REQ-OPT-304`, `REQ-OPT-305`) while strictly preserving explicit `Clone`, `Drop`, panic traps, atomics, `volatile`, `black_box` (`REQ-OPT-011`), intrinsic semantic contracts (`REQ-OPT-351`), and secure memory zeroization (`REQ-OPT-352`, `REQ-OPT-353`).

## Acceptance
- [ ] Differential run tests in `tests/run/opt_scalar` verify SCCP, GVN, CSE, DCE, checked-arithmetic trap preservation, `black_box` barrier preservation, and secure zeroization retention across `--interp`, `-O0`, `-O1`, and `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T603-report.md` with exact `## Files changed`.

## Out of scope
- Alias/escape optimization (`E15.2`), loop optimization (`E15.3`), and interprocedural inlining (`E15.4`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T603/build` and `python tools/axtest.py --compiler build-snap-T603/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:38:00 created by T215 (P15 phase planning)
- 2026-11-04 09:02:29 started (attempt 1) T603-impl
- 2026-11-04 16:58:37 accepted by QA -> done
