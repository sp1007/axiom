---
id: T965
title: E22.4 End-to-end GPU kernel execution (Vulkan/D3D12 compute + oracle differential) conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T953, T957, T961, T964]
priority: 235
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_4_host_runtime_compute]
spec: [spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, 0096, 0120, 0139, tasks/0299, tasks/0626, tasks/0843, tasks/0845, tasks/0846]
covers: [REQ-GPU-007, REQ-GPU-034, REQ-GPU-035, REQ-GPU-036, REQ-GPU-041, REQ-GPU-064, REQ-GPU-065]
---
# T965 — E22.4 End-to-end GPU kernel execution (Vulkan/D3D12 compute + oracle differential) conformance suite

## Goal
Certify the E22.4 and Phase P22 exit criterion (`ROADMAP.md` §3: kernel conformance examples run on a GPU with oracle-checked results) across `std.device`, `std.gpu`, `std.gfx`, SPIR-V codegen, Vulkan/D3D12 compute dispatch, and differential `--interp` oracle comparison.

## Scope
- Create `tests/conformance/p22/e22_4_host_runtime_compute` with end-to-end GPU compute conformance benchmarks and correctness suites comparing GPU execution results against `--interp` oracle results (`0 WEAK-NATIVE`).
- Include canonical GPU kernel workloads: (1) 1D vector SAXPY and elementwise fused polynomial pipeline (`KernelFusion`), (2) 2D tiled matrix multiplication using `SharedArray<f32, N>` and `workgroup.barrier()`, (3) parallel workgroup tree reduction + device-scope atomic histogram (`AtomicScope.Workgroup` and `AtomicScope.Device`), and (4) multi-pass `RenderGraph` / `CommandEncoder` compute + transfer DAG with `GpuEvent` synchronization.
- Verify `DeviceManager` enumeration (`REQ-GPU-064`), `GraphicsContext` / `CommandEncoder` / `RenderGraph` contracts (`REQ-GPU-065`), generational device-loss error handling (`GraphicsDeviceState.Lost`), and byte-identical numerical output between `--interp` and native GPU / software-fallback execution.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p22/e22_4_host_runtime_compute` pass in `--interp` and native modes with `0 WEAK-NATIVE` and exact oracle-checked results.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T965-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or stdlib changes; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T965/build` and `python tools/axtest.py --compiler build-snap-T965/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
