---
id: T956
title: E22.2 std.gpu.mem: DeviceBuffer, DeviceView, SharedArray, UnifiedBuffer, explicit transfers & Multi-GPU peer domains
phase: P22-gpu-heterogeneous-computing
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T955]
priority: 226
status: todo
attempts: 0
paths: [std/gpu/mem, std/gpu/transfer, std/gpu/event, tests/run/gpu_device_memory]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-131-device-memory-cross-device-ownership.md, 0120, 0139, tasks/0299, tasks/0459, tasks/0468, tasks/0470, tasks/0626]
covers: [REQ-GPU-001, REQ-GPU-002, REQ-GPU-004, REQ-GPU-017, REQ-GPU-018, REQ-GPU-020, REQ-GPU-021, REQ-GPU-022, REQ-GPU-029, REQ-GPU-030, REQ-GPU-034, REQ-GPU-035, REQ-GPU-036, REQ-GPU-038, REQ-GPU-041, REQ-GPU-042, REQ-GPU-043, REQ-GPU-044, REQ-GPU-048, REQ-GPU-049, REQ-GPU-057, REQ-GPU-059, REQ-GPU-060, REQ-GPU-061, REQ-GPU-063]
---
# T956 — E22.2 std.gpu.mem: DeviceBuffer, DeviceView, SharedArray, UnifiedBuffer, explicit transfers & Multi-GPU peer domains

## Goal
Implement `DeviceBuffer<T>`, `DeviceView<T>`, `DeviceMutView<T>`, `SharedArray<T, N>`, `ConstantBuffer<T>`, `UnifiedBuffer<T>`, explicit host↔device and multi-GPU peer transfers, and `GpuEvent` synchronization in `std/gpu/` per `spec/SPEC-131-device-memory-cross-device-ownership.md`.

## Scope
- Implement `std/gpu/mem`: owned `DeviceBuffer<T>` (`alloc`, `from_slice`, `len`, `capacity`, `view`, `mut_view`, `sub_view`, `split_at_mut`, `Drop`), non-owning `DeviceView<T>` and `DeviceMutView<T>`, workgroup-scoped `SharedArray<T, N>`, read-only `ConstantBuffer<T>`, `PinnedHostBuffer<T>`, and `UnifiedBuffer<T>` requiring explicit domain acquire/release synchronization (`0139 §XX.9-14`).
- Implement `std/gpu/transfer`: explicit synchronous and asynchronous transfer operations (`upload`, `download`, `upload_async`, `download_async`, `device_copy`), explicit storage-domain migration methods (`.to(device)`, `.to_async(device)` for device buffers and tensors per `ATENSOR-29`, `ATENSOR-42-44`), multi-GPU `can_access_peer(src, dst)` and `peer_copy` / `peer_copy_async` validating explicit `DeviceId` peer access capability with automatic pinned-host staging fallback when direct P2P is unavailable (`APAR-63-64`, `tasks/0626 §41`), `ShardedDeviceBuffer<T>` (`scatter`, `gather`, `replicate`, `shard_view(rank)`) for data-parallel and tensor-parallel AI/compute workloads across multiple GPUs, and multi-GPU collective operations (`all_reduce`, `all_gather`, `reduce_scatter`, `broadcast` over `ReduceOp = Sum | Mean | Max | Min`).
- Implement `std/gpu/event`: `GpuEvent` state machine (`Pending`, `Completed`, `Failed`), blocking `.wait() -> Result<Unit, GpuError>` establishing `synchronizes-with` happens-before edges (`AGPU-13`, `0139 §XX.15-18, §XX.40`), and optional non-mandatory `Future` adapter `.into_future()` (`0139 §XX.39`).
- Implement Unified Memory Architecture support (ADR-0040): `UnifiedBuffer<T>` and `std/gpu/transfer` elide copies on `is_unified_memory` devices (domain-state transitions + barriers / cache flush-invalidate on `NonCoherentUma` only), `TransferStats` reporting actually-copied bytes, `UnifiedBuffer.from_mmap` / `from_virtual_region` zero-copy page import (E21.6 `T921`/`T922` mappings; `GpuError.HostImportUnsupported` rather than a silent copy), `shared_read_views()`, and `device.memory_budget() -> GpuMemoryBudget { unified_pool_total_bytes, recommended_max_working_set_bytes, current_allocated_bytes, pressure }` with `GpuError.OutOfUnifiedMemoryBudget` on over-allocation.
- Add run tests in `tests/run/gpu_device_memory` exercising device allocation, views, disjoint mutable splits, explicit transfers, multi-GPU domain isolation, and `GpuEvent` lifetime tracking.

## Acceptance
- [ ] Run tests in `tests/run/gpu_device_memory` pass in `--interp` and native modes with `0 WEAK-NATIVE`, verifying explicit transfers, `DeviceView`/`DeviceMutView` bounds and disjointness, multi-GPU peer transfer checks, and `GpuEvent` happens-before visibility.
- [ ] On a mock `CacheCoherentUma` / `NonCoherentUma` adapter, `upload` / `download` / `.to(device)` report `TransferStats.bytes_copied == 0` with results identical to the `Discrete` path; `from_mmap` imports without allocation; exceeding the budget returns `GpuError.OutOfUnifiedMemoryBudget`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T956-report.md` with exact `## Files changed`.

## Out of scope
- SPIR-V binary codegen (`E22.3`) and Vulkan/D3D12 OS driver backends (`E22.4`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T956/build` and `python tools/axtest.py --compiler build-snap-T956/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
