---
id: T952
title: E22.1 Kernel MIR body, SIMT grid/workgroup intrinsics, scoped atomics & oracle grid executor
phase: P22-gpu-heterogeneous-computing
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T951]
priority: 222
status: todo
attempts: 0
paths: [compiler/mir/gpu_kernel, compiler/interp/gpu_sim, std/gpu/kernel, tests/run/gpu_kernel_model]
locks: [compiler/mir/mir.ax, compiler/mir/verifier.ax, compiler/interp/interp.ax]
spec: [spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-31-atomics.md, 0128, 0139, 0162, tasks/0299, tasks/0470, tasks/0626]
covers: [REQ-GPU-005, REQ-GPU-023, REQ-GPU-044, REQ-GPU-045, REQ-GPU-055, REQ-GPU-056, REQ-GPU-062]
---
# T952 — E22.1 Kernel MIR body, SIMT grid/workgroup intrinsics, scoped atomics & oracle grid executor

## Goal
Implement `BodyKind.Kernel` MIR lowering, SIMT grid/workgroup intrinsics, collective barrier uniformity and cross-lane race verification, scoped GPU atomics (`AtomicScope`), and the deterministic MIR oracle lockstep SIMT grid simulator.

## Scope
- Lower `@kernel` functions to `BodyKind.Kernel` (`SPEC-04 AXS-EXT-040`, `0162 §33`) in `compiler/mir/gpu_kernel` and expose `std/gpu/kernel` primitives (`global_id`, `local_id`, `group_id`, `local_size`, `global_size`, `num_groups`, `workgroup_barrier`, `memory_fence`, and scoped `atomic_load`/`atomic_store`/`atomic_rmw`/`atomic_cas` with `AtomicScope = Thread | Workgroup | Device | System`; `0128 §63-66`, `AATOM-38`).
- Extend the MIR verifier (`compiler/mir/verifier.ax` and `compiler/mir/gpu_kernel`) to enforce uniform control flow across `workgroup_barrier` (rejecting barriers inside lane-divergent branches; `0139 §XX.20-21`, `AGPU-12`), forbid reordering memory operations across barriers, and check `KernelProof` lane-indexing bounds and cross-lane write-write race freedom (`tasks/0626 §31-33`).
- Implement the deterministic multi-workgroup, multi-lane lockstep SIMT kernel executor in `compiler/interp/gpu_sim`: execute workgroup invocations across barrier phases in `--interp`, detecting barrier divergence and un-synchronized cross-lane read/write or write/write races on `Device`/`Shared` memory.
- Add run and negative tests in `tests/run/gpu_kernel_model`.

## Acceptance
- [ ] Run tests in `tests/run/gpu_kernel_model` verify SIMT 1D/2D/3D indexing (`global_id`, `local_id`, `group_id`), `workgroup_barrier` synchronization, and scoped GPU atomic operations (`Workgroup`, `Device`, `System`), and negative tests confirm divergent barriers and un-synchronized cross-lane data races are rejected.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T952-report.md` with exact `## Files changed`.

## Out of scope
- Device memory buffer/view types and cross-device transfers (`E22.2`, `T954`–`T957`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T952/build` and `python tools/axtest.py --compiler build-snap-T952/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
