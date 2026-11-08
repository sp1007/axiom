---
id: T618
title: E15.5 — Straight-line SLP vectorization, target SIMD width/cost model & LIR vector lowering
phase: P15-optimizer-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T463, T617]
priority: 112
status: todo
attempts: 0
paths: [compiler/opt/slp, compiler/lir/vec_lower, tests/run/opt_slp_vec]
spec: [spec/SPEC-74-auto-vectorization.md, 0095, 0162, tasks/0403, tasks/0406, tasks/0407]
covers: [REQ-OPT-213, REQ-OPT-214, REQ-OPT-215, REQ-OPT-216, REQ-OPT-217]
---
# T618 — E15.5 — Straight-line SLP vectorization, target SIMD width/cost model & LIR vector lowering

## Goal
Implement Superword-Level Parallelism (`SLP`) straight-line basic-block vectorization, the target-aware SIMD profitability cost model, and `OptIR` → LIR vector lowering in `compiler/opt/slp` and `compiler/lir/vec_lower`.

## Scope
- Implement `SLP` pack-tree discovery in `compiler/opt/slp` seeded from adjacent struct-field or array-element stores/reductions, verifying isomorphic operations and `MemorySSA` independence (`REQ-OPT-215..217`).
- Implement the target SIMD cost model comparing vector execution latency/throughput plus pack/extract overhead against scalar cost on the declared target profile (`REQ-OPT-213`, `REQ-OPT-214`).
- Lower auto-vectorized loop and `SLP` operations in `compiler/lir/vec_lower` to canonical LIR vector registers (`Vec128`/`Vec256`) and unaligned/aligned vector loads/stores consumed by the P12 SIMD backend.

## Acceptance
- [ ] Differential run and LIR/machine dump tests in `tests/run/opt_slp_vec` verify `SLP` packing of 2/4/8-lane adjacent field/array operations into `XMM`/`YMM` instructions and verify cost-model rejection of unprofitable scatter/gather packs.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T618-report.md` with exact `## Files changed`.

## Out of scope
- Manual SIMD intrinsics (delivered in P12) and whole-program LTO (`E15.6`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`); depends on P12 gate `T312` (`ROADMAP.md` §3/§4).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T618/build` and `python tools/axtest.py --compiler build-snap-T618/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:42:00 created by T215 (P15 phase planning)
