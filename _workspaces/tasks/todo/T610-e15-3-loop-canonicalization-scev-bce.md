---
id: T610
title: E15.3 — Natural loop discovery, loop canonicalization, Scalar Evolution (SCEV) & range/bounds-check elimination (BCE)
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T606, T609]
priority: 103
status: todo
attempts: 0
paths: [compiler/opt/loops, compiler/opt/bce, tests/run/opt_bce]
spec: [spec/SPEC-72-loops-scev-bce.md, 0113, 0165, tasks/0366, tasks/0402, tasks/0416, tasks/0549]
covers: [REQ-OPT-143, REQ-OPT-144, REQ-OPT-145, REQ-OPT-146, REQ-OPT-147, REQ-OPT-155, REQ-OPT-156, REQ-OPT-157, REQ-OPT-158, REQ-OPT-159, REQ-OPT-160, REQ-OPT-161, REQ-OPT-162, REQ-OPT-189, REQ-OPT-190, REQ-OPT-342]
---
# T610 — E15.3 — Natural loop discovery, loop canonicalization, Scalar Evolution (SCEV) & range/bounds-check elimination (BCE)

## Goal
Implement CFG natural loop discovery, preheader/latch/LCSSA canonicalization, overflow-faithful Scalar Evolution (`SCEV`), dominating range analysis (`RangeInfo`), and Bounds-Check Elimination (`BCE`) in `compiler/opt/loops` and `compiler/opt/bce`.

## Scope
- Implement natural loop detection, loop nesting forest, preheader/latch insertion, and LCSSA form in `compiler/opt/loops`, preserving `Drop`, ownership, capability, synchronization, async suspension, and FFI boundaries (`REQ-OPT-155..162`).
- Implement `SCEV` affine add-recurrence analysis (`{start, +, step}`) respecting checked vs wrapping integer semantics and computing proven trip counts.
- Implement `RangeInfo` and `BCE` in `compiler/opt/bce` (`REQ-OPT-189`, `REQ-OPT-190`, `REQ-OPT-342`) to eliminate proven in-bounds array, `view<[T]>`, `mut_view<[T]>`, and `Vec<T>` index checks while retaining checks for any `Unknown` or potentially out-of-bounds index.
- Validate `MemorySSA` and `EffectInfo` loop dependencies (`REQ-OPT-143..147`).

## Acceptance
- [ ] Differential run and `OptIR` dump tests in `tests/run/opt_bce` verify elimination of proven bounds checks in `for i in 0..len(a)` and guarded slices, and verify that out-of-bounds accesses still panic identically at `-O0`, `-O1`, and `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T610-report.md` with exact `## Files changed`.

## Out of scope
- Loop-invariant code motion, unrolling/peeling, and iterator fusion (`T611`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T610/build` and `python tools/axtest.py --compiler build-snap-T610/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:40:00 created by T215 (P15 phase planning)
