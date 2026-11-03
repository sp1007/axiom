---
id: T958
title: E22.3 Canonical Axiom GPU IR (AGIR), kernel fusion & SPIR-V 1.6 compute backend specification (SPEC-132)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T954]
priority: 228
status: todo
attempts: 0
paths: [spec/SPEC-132-gpu-ir-spirv-codegen-backend.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-81-target-desc-isa-conformance.md, 0096, 0139, 0162, tasks/0626]
covers: [REQ-GPU-005, REQ-GPU-007, REQ-GPU-023, REQ-GPU-024, REQ-GPU-032, REQ-GPU-045, REQ-GPU-046, REQ-GPU-047, REQ-GPU-052, REQ-GPU-053, REQ-GPU-054, REQ-GPU-055]
---
# T958 — E22.3 Canonical Axiom GPU IR (AGIR), kernel fusion & SPIR-V 1.6 compute backend specification (SPEC-132)

## Goal
Consolidate the canonical specification for Axiom's GPU Intermediate Representation (`AGIR`), `GpuKernelABI` descriptor/push-constant layout, proof-preserving kernel fusion & transfer optimizations, and the SPIR-V 1.6 compute codegen backend into `spec/SPEC-132-gpu-ir-spirv-codegen-backend.md` (`AXS-SPIRV-*` rule IDs).

## Scope
- Write `spec/SPEC-132-gpu-ir-spirv-codegen-backend.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-SPIRV-NNN` rules (`0096 §3, §20-26`, `0139 §XX.24, §XX.34-36, §XX.42-43`, `0162 §32-33`, `tasks/0626 §20-38, §43`).
- Specify the Axiom GPU Intermediate Representation (`AGIR`, `tasks/0626 §22-23`): preserving explicit storage domains/address spaces (`StorageBuffer`, `Workgroup`, `UniformConstant`, `Function`, `Private`, `PushConstant`), SIMT built-ins (`GlobalInvocationId`, `LocalInvocationId`, `WorkgroupId`, `NumWorkgroups`, `WorkgroupSize`), scoped barriers, and scoped atomics.
- Specify `GpuKernelABI` and `CallConv.GpuKernel` (`SPEC-04 AXS-EXT-052`, `0139 §XX.24, §XX.43`, `tasks/0626 §20`): deterministic mapping of `DeviceView<T>` / `DeviceMutView<T>` parameters to storage-buffer descriptor bindings (`(set = 0, binding = i)` plus length/stride metadata), scalar/small-struct parameters to push constants or uniform blocks, and `SharedArray` workgroup memory sizing.
- Specify proof-preserving `ExecutionGraph` and `AGIR` optimizations (`0139 §XX.34-36, §XX.42`, `tasks/0626 §24-30, §37-38`, `AGPU-18..22`, `AGPU-27..29`, `AGPU-51`): producer-consumer elementwise `KernelFusion`, redundant host↔device transfer elimination, shared/register memory promotion, and `GpuCostModel`/occupancy estimation, requiring post-pass re-verification and preserving observable atomic/barrier/error semantics.
- Specify the SPIR-V 1.6 compute module binary format (`ObjectFormat.SpirV`, `SPEC-04 AXS-EXT-070`): magic word `0x07230203`, version `1.6` (`0x00010600`), `OpCapability Shader` / `VulkanMemoryModel` / `VulkanMemoryModelDeviceScope`, `OpMemoryModel Logical Vulkan`, structured control-flow headers (`OpLoopMerge`, `OpSelectionMerge`), scoped `OpControlBarrier` / `OpMemoryBarrier` / `OpAtomic*` instructions, kernel reflection metadata section, and the mandatory internal SPIR-V module validator.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-132-gpu-ir-spirv-codegen-backend.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-SPIRV-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T958-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of `AGIR` optimization passes and SPIR-V binary emission (`T959`–`T960`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T958/build` and `python tools/axtest.py --compiler build-snap-T958/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
