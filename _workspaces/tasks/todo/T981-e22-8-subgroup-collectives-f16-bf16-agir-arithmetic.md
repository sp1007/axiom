---
id: T981
title: E22.8 Capability-gated SIMT Subgroup collectives & f16/bf16 device arithmetic in AGIR
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T959, T980]
priority: 251
status: todo
attempts: 0
paths: [compiler/agir/subgroups, compiler/types/half_precision, tests/agir/subgroups, tests/agir/half]
locks: [compiler/agir/ir.ax, compiler/types/type.ax]
spec: [spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md, 0096, 0139, tasks/0470]
covers: [REQ-GPU-023, REQ-GPU-045, REQ-GPU-062, REQ-GPU-064]
---
# T981 — E22.8 Capability-gated SIMT Subgroup collectives & f16/bf16 device arithmetic in AGIR

## Goal
Implement capability-gated SIMT Subgroup collective intrinsics and half-precision (`f16`, `bf16`) device floating-point types in AGIR (`compiler/agir/subgroups`, `compiler/types/half_precision`), enabling high-efficiency warp-level communication for AI workloads without thread divergence bugs.

## Scope
- Implement `f16` and `bf16` types in `compiler/types/half_precision` and `compiler/types/type.ax`:
  - 16-bit float storage formats and conversion operations (`f16 as f32`, `f32 as f16`, `bf16 as f32`).
  - Arithmetic operations: addition, subtraction, multiplication, division, FMA (`fma(a, b, c)`), fast reciprocal square root.
  - Vector types: `f16x2`, `f16x4`, `f16x8`, `bf16x2`, `bf16x4`.
- Implement Subgroup SIMT intrinsics in `compiler/agir/subgroups` and `compiler/agir/ir.ax` (`REQ-GPU-045`, `REQ-GPU-062`):
  - Identification: `subgroup.size()`, `subgroup.invocation_id()`.
  - Shuffle and broadcast: `subgroup.broadcast(val, id)`, `subgroup.shuffle(val, delta)`, `subgroup.shuffle_xor(val, mask)`.
  - Ballots and predicates: `subgroup.ballot(predicate)` returning 64-bit/128-bit bitmask, `subgroup.all(predicate)`, `subgroup.any(predicate)`.
  - Reductions: `subgroup.reduce_add(val)`, `subgroup.reduce_min(val)`, `subgroup.reduce_max(val)`.
- Enforce capability gating in the type checker:
  - Verify that subgroup operations are only invoked within `@kernel` execution domains on devices reporting `Capability.Subgroups`.
  - Reject divergent control flow around non-uniform subgroup operations where hardware requires uniform convergence (`REQ-GPU-023`).
- Lower subgroup and half-precision operations to SPIR-V (`OpGroupNonUniform*`, `OpCapability SubgroupBallotKHR`, `Float16`), HLSL (`WaveGetLaneIndex()`, `WaveReadLaneAt()`, `WaveActiveBallot()`, `half`), and MSL (`simdgroup_barrier`, `simd_shuffle`, `simd_broadcast`, `half`).
- Add unit tests in `tests/agir/subgroups` and `tests/agir/half`.

## Acceptance
- [ ] Tests in `tests/agir/subgroups` verify that warp-level collectives lower to corresponding backend instructions across SPIR-V, HLSL, and MSL.
- [ ] Tests in `tests/agir/half` verify numerical accuracy of `f16` and `bf16` arithmetic against reference values.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T981-report.md` with exact `## Files changed`.

## Out of scope
- Cooperative Matrix MMA tile instructions (`T982`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.8.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T981/build` and `python tools/axtest.py --compiler build-snap-T981/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 AI & Hot-Reload expansion)
