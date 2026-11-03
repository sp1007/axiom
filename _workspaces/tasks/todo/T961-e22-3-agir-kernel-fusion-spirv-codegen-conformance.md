---
id: T961
title: E22.3 AGIR optimization, kernel fusion & SPIR-V 1.6 binary codegen conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T960]
priority: 231
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_3_spirv_codegen]
spec: [spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, 0096, 0139, 0162, tasks/0626]
covers: [REQ-GPU-005, REQ-GPU-023, REQ-GPU-032, REQ-GPU-045, REQ-GPU-046, REQ-GPU-047, REQ-GPU-052, REQ-GPU-053, REQ-GPU-054, REQ-GPU-055]
---
# T961 — E22.3 AGIR optimization, kernel fusion & SPIR-V 1.6 binary codegen conformance suite

## Goal
Certify E22.3 exit criteria with an end-to-end conformance suite covering `AGIR` lowering, `GpuKernelABI` descriptor/push-constant layouts, proof-preserving `KernelFusion` (`AGPU-51`), non-collapsed GPU address spaces (`0162 §32-33`), and SPIR-V 1.6 binary emission and validation.

## Scope
- Create `tests/conformance/p22/e22_3_spirv_codegen` testing every rule in `spec/SPEC-132-gpu-ir-spirv-codegen-backend.md`.
- Verify SPIR-V 1.6 binary codegen for scalar, vector (`f32x4`, `i32x4`), struct, array, `SharedArray`, and `ConstantBuffer` kernels, checking explicit `StorageBuffer`, `Workgroup`, `UniformConstant`, `PushConstant`, and `Function` storage classes (`0162 §32-33`).
- Verify structured CFG emission (`OpLoopMerge` and `OpSelectionMerge`) on nested loops, `break`/`continue`, `match` switches, and uniform `workgroup.barrier()` calls.
- Verify semantic equivalence between unfused and fused multi-kernel chains (`AGPU-19`, `AGPU-51`) and verify that kernel specialization re-runs semantic and `AGIR` verification (`AGPU-20`, `AGPU-29`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p22/e22_3_spirv_codegen` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T961-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or stdlib changes; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T961/build` and `python tools/axtest.py --compiler build-snap-T961/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
