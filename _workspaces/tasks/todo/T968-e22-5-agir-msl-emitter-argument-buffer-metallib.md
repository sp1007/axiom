---
id: T968
title: E22.5 AGIR -> MSL (.metal) source emitter, argument buffer reflection & metallib pipeline
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T959, T967]
priority: 238
status: todo
attempts: 0
paths: [compiler/target/msl, compiler/obj/metallib, tests/target/msl]
locks: [compiler/target/desc.ax, compiler/obj/obj.ax]
spec: [spec/SPEC-134-apple-metal-msl-backend.md, 0096, 0139, 0162, tasks/0846]
covers: [REQ-GPU-007, REQ-GPU-054, REQ-GPU-055, REQ-GPU-065]
---
# T968 — E22.5 AGIR -> MSL (.metal) source emitter, argument buffer reflection & metallib pipeline

## Goal
Implement the Metal Shading Language source code generator and offline `.metallib` pipeline in `compiler/target/msl` and `compiler/obj/metallib`: lowering AGIR compute functions to clean MSL 3.x, generating argument buffer reflection metadata, and producing verifiable Metal libraries.

## Scope
- Register the Apple Metal target in `compiler/target/msl` and `compiler/target/desc.ax` (`SPEC-04 AXS-EXT-052/060/070`, `ObjectFormat.MetalLib`, `CallConv.GpuKernel`).
- Implement the AGIR to MSL source emitter in `compiler/target/msl`:
  - Map address spaces to Metal pointer qualifiers: `StorageBuffer` to `device`, `UniformConstant` to `constant`, `Workgroup` to `threadgroup`, local variables to `thread` (`REQ-GPU-054`).
  - Map SIMT built-ins to Metal attributes: `uint3 thread_pos [[thread_position_in_grid]]`, `uint3 group_pos [[threadgroup_position_in_grid]]`, `uint3 thread_in_group [[thread_position_in_threadgroup]]`, `uint3 group_size [[threads_per_threadgroup]]`.
  - Map memory barriers to `threadgroup_barrier(mem_flags::mem_device | mem_flags::mem_threadgroup)`.
  - Map atomic operations to `metal::atomic<T>` operations with memory order parameters (`memory_order_relaxed`, `memory_order_acq_rel`).
- Implement argument binding and parameter layout:
  - Assign explicit `[[buffer(n)]]` attributes starting from index 0 for all `DeviceView<T>` and `DeviceMutView<T>` kernel arguments.
  - Pack scalar/struct uniforms into an immutable `constant Params& params [[buffer(N)]]` block.
  - Generate deterministic reflection metadata describing argument count, buffer index bindings, sizes, and workgroup size constraints.
- Implement the `.metallib` offline compiler integration in `compiler/obj/metallib`: invoke `xcrun -sdk macosx metal -c` / `metallib` when available on macOS hosts, or package raw MSL source into standard Axiom archive wrappers for runtime JIT compilation on target devices.
- Add MSL emission and syntax validation tests in `tests/target/msl`.

## Acceptance
- [ ] Tests in `tests/target/msl` verify `@kernel` functions produce syntactically valid MSL 3.x code with correct headers (`#include <metal_stdlib>`), namespace usage (`using namespace metal;`), address spaces, barriers, and `[[buffer(n)]]` attributes.
- [ ] Argument buffer reflection tables match parameter signatures exactly.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T968-report.md` with exact `## Files changed`.

## Out of scope
- Host driver execution using Metal framework (`T969`).
- Raster graphics shader stages (`@vertex`, `@fragment` in `E22.6`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.5.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T968/build` and `python tools/axtest.py --compiler build-snap-T968/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Metal expansion)
