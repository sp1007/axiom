---
id: T960
title: E22.3 SPIR-V 1.6 binary emitter, descriptor reflection metadata & internal SPIR-V module validator
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T959]
priority: 230
status: todo
attempts: 0
paths: [compiler/target/spirv, compiler/obj/spirv, tests/obj/spirv, tests/mc/spirv]
locks: [compiler/target/desc.ax, compiler/obj/obj.ax]
spec: [spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-81-target-desc-isa-conformance.md, 0162, tasks/0626]
covers: [REQ-GPU-005, REQ-GPU-023, REQ-GPU-054, REQ-GPU-055]
---
# T960 — E22.3 SPIR-V 1.6 binary emitter, descriptor reflection metadata & internal SPIR-V module validator

## Goal
Implement the SPIR-V 1.6 compute target (`TargetDesc`, `ObjectFormat.SpirV`, `CallConv.GpuKernel`), deterministic binary `.spv` module writer, kernel reflection metadata table, and internal SPIR-V structural/SSA/address-space validator in `compiler/`.

## Scope
- Register the SPIR-V compute target in `compiler/target/spirv` and `compiler/target/desc.ax` (`SPEC-04 AXS-EXT-052/060/070`, `ObjectFormat.SpirV`, `CallConv.GpuKernel`).
- Implement the binary SPIR-V 1.6 emitter in `compiler/obj/spirv`: emit the 5-word header (`0x07230203`, version `0x00010600`, generator magic, bound, schema `0`) and sections in canonical SPIR-V logical layout order (`OpCapability`, `OpExtension`, `OpExtInstImport`, `OpMemoryModel Logical Vulkan`, `OpEntryPoint GLCompute`, `OpExecutionMode LocalSize`, debug names, `DescriptorSet`/`Binding`/`ArrayStride`/`Block`/`Offset` decorations, type/constant/global declarations, and function bodies with `OpLoopMerge`/`OpSelectionMerge`, `OpControlBarrier`, `OpMemoryBarrier`, and scoped `OpAtomic*`).
- Emit deterministic `GpuKernelABI` reflection metadata alongside `.spv` modules (entry-point names, workgroup dimensions, descriptor set/binding table, push-constant ranges, shared memory byte size, required device features).
- Implement the built-in SPIR-V module validator in `compiler/obj/spirv` checking SSA dominance, ID bounds, section ordering, explicit storage-class matching on `OpTypePointer`/`OpLoad`/`OpStore`/`OpAccessChain` (`0162 §32`), and `OpLoopMerge`/`OpSelectionMerge` structural rules before writing output bytes.
- Add binary module, disassembly, and validator tests in `tests/obj/spirv` and `tests/mc/spirv`.

## Acceptance
- [ ] Tests in `tests/obj/spirv` and `tests/mc/spirv` verify that `@kernel` functions compile to deterministic, byte-reproducible `.spv` binaries with valid headers, capabilities, explicit storage classes, structured control flow, scoped atomics/barriers, and accurate reflection metadata, and pass the internal SPIR-V validator.
- [ ] Negative validator tests confirm malformed storage classes, unstructured loops, or invalid SSA IDs are caught by the internal SPIR-V validator.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T960-report.md` with exact `## Files changed`.

## Out of scope
- Host Vulkan/D3D12 compute runtime dispatch (`E22.4`, `T962`–`T965`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T960/build` and `python tools/axtest.py --compiler build-snap-T960/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
