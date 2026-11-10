---
id: T954
title: E22.2 Canonical device memory spaces, DeviceBuffer/DeviceView ownership & async event lifetime specification (SPEC-131)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T950]
priority: 224
status: todo
attempts: 0
paths: [spec/SPEC-131-device-memory-cross-device-ownership.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/SPEC-51-raw-memory-volatile-mmio-layout.md, spec/requirements/OWNER.md, 0120, 0139, 0162, tasks/0299, tasks/0459, tasks/0468, tasks/0470, tasks/0626]
covers: [REQ-OWNER-009, REQ-OPT-347, REQ-GPU-001, REQ-GPU-002, REQ-GPU-004, REQ-GPU-007, REQ-GPU-015, REQ-GPU-016, REQ-GPU-017, REQ-GPU-018, REQ-GPU-019, REQ-GPU-020, REQ-GPU-021, REQ-GPU-022, REQ-GPU-029, REQ-GPU-030, REQ-GPU-031, REQ-GPU-033, REQ-GPU-034, REQ-GPU-035, REQ-GPU-036, REQ-GPU-038, REQ-GPU-039, REQ-GPU-040, REQ-GPU-041, REQ-GPU-042, REQ-GPU-043, REQ-GPU-044, REQ-GPU-048, REQ-GPU-049, REQ-GPU-050, REQ-GPU-051, REQ-GPU-057, REQ-GPU-059, REQ-GPU-060, REQ-GPU-061, REQ-GPU-063]
---
# T954 — E22.2 Canonical device memory spaces, DeviceBuffer/DeviceView ownership & async event lifetime specification (SPEC-131)

## Goal
Consolidate the canonical specification for Axiom's GPU/accelerator storage and address spaces, unified CPU/GPU ownership and capability model, `DeviceBuffer<T>` / `DeviceView<T>` / `DeviceMutView<T>`, explicit host↔device and peer-device transfers, and in-flight `InFlight<B>` resource lifetime retention into `spec/SPEC-131-device-memory-cross-device-ownership.md` (`AXS-GMEM-*` rule IDs).

## Scope
- Write `spec/SPEC-131-device-memory-cross-device-ownership.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GMEM-NNN` rules (`0120 §265-274`, `0139 §XX.6-XX.18, §XX.31-XX.44`, `0162 §32-33`, `tasks/0299 §7-23`, `tasks/0626 §6-19`).
- Specify semantic storage and address spaces (`Host = 0`, `Device = 1`, `Shared = 2`, `Constant = 3`, `Local = 4`, `Private = 5`, `External = 6` matching `SPEC-04 AXS-EXT-020/042/051` and `SPEC-51`), requiring backends and LIR to preserve non-generic address spaces (`0162 §32-33`) and forbidding implicit host↔device pointer or view conversions (`AGPU-21`, `0139 §XX.7-8`).
- Specify the unified ownership and capability contract across domains (`AGPU-20`, `AGPU-57..59`): `DeviceBuffer<T>` owns device storage without runtime object headers (`AGPU-24`), `DeviceView<T>` (`view<T @device>`) and `DeviceMutView<T>` (`mut_view<T @device>`) are non-owning capabilities obeying standard exclusive-mutable aliasing and disjointness rules (`0139 §XX.9-11`), and `SharedArray<T, N>` cannot escape workgroup scope (`tasks/0626 §17`).
- Specify explicit host↔device, device↔device, and multi-GPU peer/collective transfer contracts (`upload`, `download`, `upload_async`, `download_async`, `device_copy`, `can_access_peer`, `peer_copy`, `peer_copy_async`, and tensor `.to(device)` / `.to_async(device)` per `ATENSOR-29`, `APAR-63-64`), `ShardedDeviceBuffer<T>` (`ShardStrategy = DataParallel { axis: usize } | TensorParallel { axis: usize } | Replicated | PipelineStage`) for partitioning AI/ML tensors and compute buffers across multiple GPUs simultaneously, multi-GPU collective primitives (`all_reduce`, `all_gather`, `reduce_scatter`, `broadcast` with `ReduceOp = Sum | Mean | Max | Min`), plus `UnifiedBuffer<T>` cross-domain synchronization (`0139 §XX.12-14`).
- Specify in-flight asynchronous operation lifetime and `Drop`/relocation safety (`AGPU-23`, `AGPU-33`, `0139 §XX.15-17, §XX.31`, `ADR-0040` §2): specify in-flight access as ownership transfer into `InFlight<B>`; `InFlight<B>.wait(self) -> (B, Result<Unit, GpuError>)` returns the buffer on both success and failure (ownership preserved on `DeviceLost`); `Drop for InFlight<B>` blocks deterministically until completion; `InFlight<B>` contains no views and is legal across `.await` (`AXS-ASY-034`).
- Specify Unified Memory Architecture (UMA) and Memory Topology semantics per ADR-0040 revision and REQ-OWNER-009:
  - Orthogonal memory topology: `GpuMemoryTopology = DiscretePool | UnifiedSystemPool | CoherentMultiPoolNuma`, per-heap `HeapFlags = DeviceLocal | HostVisible | HostCoherent | HostCached`, and `rebar_aperture_bytes: u64` (> 256 MiB distinguishing full ReBAR from legacy 256 MiB PCIe BAR aperture).
  - Single ownership model mapping (AXS-GMEM-020): `HostExclusive` = host holds `OWNED` or `mut_view`; `DeviceExclusive` = ownership moved into `InFlight<B>`; `SharedRead` = concurrent host `view<T>` and `DeviceView<T>` under `AXS-CAP-003`. No separate 3-state typestate machine.
  - Value-preserving copy elision (AXS-GMEM-021): `upload`/`download`/`device_copy` strictly preserve value copy semantics on every machine (RAM→RAM `memcpy` without staging on UMA). Copy elision applies strictly to domain handoffs on the same `UnifiedBuffer<T>`, by-value `.into_device(self)`, by-value `.to(device)` (REQ-OPT-347), and `shared_read_views()`. Explicitly exclude 2D/3D tiled/swizzled textures from linear zero-copy claims.
  - Type-safe host memory import (AXS-GMEM-022): `HostImport.read<T: PlainData>`, `HostImport.write<T: PlainData>`, `HostImport.region<T: PlainData>` returning non-owning stored views (`ImportedDeviceView<T>` / `ImportedDeviceMutView<T>`), borrowing `Mmap`/`VirtualRegion`.
  - Hardware-independent race check (AXS-GMEM-023): access rules apply identically to all host-accessible memory across all topologies. Violations report `AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, or `AX_GPU_HOST_DEVICE_ACCESS_CONFLICT` with note `gpu_in_flight`.
  - Multi-adapter UMA + dGPU in one process (AXS-GMEM-025): `UnifiedBuffer` is owned by host domain and bound per-device via `bind_to(device) -> DeviceView<T>`.
  - Unified budget and policy (AXS-GMEM-026): single error `GpuError.OutOfDeviceMemory { requested_bytes: u64, budget: GpuMemoryBudget }` with `AllocPolicy = Advisory | StrictBudget`.
- Register `AX_GPU_HOST_DEVICE_ACCESS_CONFLICT` in `spec/diagnostics.md` §3 and §11 with emitting task `T955`.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-131-device-memory-cross-device-ownership.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-GMEM-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] SPEC-131 contains numbered `AXS-GMEM-*` rules for: single ownership model mapping of domain states, copy-elision legality (linear buffers only, excluding tiled textures), `InFlight<B>` ownership token lifecycle, type-safe host import typing/hazards, hardware-independent portability contract, and unified budget policy with positive/negative examples.
- [ ] `spec/diagnostics.md` registers `AX_GPU_HOST_DEVICE_ACCESS_CONFLICT` under the `GPU` area with emitting task `T955`.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T954-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and stdlib implementation of device memory ownership and transfers (`T955`–`T956`, `T990`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T954/build` and `python tools/axtest.py --compiler build-snap-T954/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: single ownership mapping, InFlight token, value-preserving copy elision, REQ-OWNER-009)
