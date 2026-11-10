---
id: T990
title: E22.10 std.gpu.uma: UnifiedBuffer domain handoff, copy elision & HostImport types
phase: P22-gpu-heterogeneous-computing
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T921, T922, T956, T989]
priority: 260
status: todo
attempts: 0
paths: [std/gpu/uma, tests/run/gpu_uma_transfer]
locks: [std/gpu/mod.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-139-unified-memory-architecture.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/requirements/OWNER.md]
covers: [REQ-OWNER-009, REQ-OPT-347, REQ-GPU-035]
---
# T990 — E22.10 std.gpu.uma: UnifiedBuffer domain handoff, copy elision & HostImport types

## Goal
Implement the high-level `std/gpu/uma` module providing `UnifiedBuffer<T>` domain handoffs, value-preserving copy elision, `shared_read_views()`, `HostAccessPattern`, and type-safe `HostImport` APIs per `spec/SPEC-139-unified-memory-architecture.md`.

## Scope
- Implement `std/gpu/uma`:
  - `UnifiedBuffer<T>` methods: `alloc(len, access: HostAccessPattern) -> Result<UnifiedBuffer<T>, GpuError>`, `into_device(self) -> DeviceBuffer<T>`, and `DeviceBuffer.into_host(self) -> UnifiedBuffer<T>` when supported by topology; acquire/release domain transitions without copying memory.
  - `shared_read_views(view<UnifiedBuffer<T>>) -> (view<T>, DeviceView<T>)` enabling concurrent CPU and GPU read access to the same physical memory without locking or copying.
  - `HostAccessPattern = WriteOnly | ReadOnly | ReadWrite` attributes configuring CPU caching properties (`WRITE_COMBINE` vs `WRITE_BACK` / `HOST_CACHED`).
  - `HostImport` struct:
    - `HostImport.read<T: PlainData>(src: view<Mmap>) -> Result<ImportedDeviceView<T>, GpuError>`
    - `HostImport.write<T: PlainData>(src: mut_view<MmapMut>) -> Result<ImportedDeviceMutView<T>, GpuError>`
    - `HostImport.region<T: PlainData>(src: mut_view<VirtualRegion>, offset: usize, len: usize) -> Result<ImportedDeviceMutView<T>, GpuError>`
  - Non-owning stored views `ImportedDeviceView<T>` and `ImportedDeviceMutView<T>`: borrowing source mapping with static outlives enforcement (`AXS-CAP-006`); verifying alignment (`offset % align_of::<T>() == 0`, `len % size_of::<T>() == 0`), returning `GpuError.HostImportMisaligned`.
  - `TransferStats`: recording `bytes_copied`, `bytes_written_over_bus`, `cache_flushes`, `cache_invalidates`.
- Add run tests in `tests/run/gpu_uma_transfer` exercising domain handoffs, copy elision, `shared_read_views`, and `HostImport` validation.

## Acceptance
- [ ] Run tests in `tests/run/gpu_uma_transfer` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] `UnifiedBuffer` domain transitions and `.into_device(self)` report `TransferStats.bytes_copied == 0`.
- [ ] `HostImport.read`, `write`, and `region` correctly wrap `Mmap`/`VirtualRegion` without allocating new memory, and reject misaligned or non-PlainData types.
- [ ] `shared_read_views()` permits simultaneous CPU and GPU read access with identical byte observations.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T990-report.md` with exact `## Files changed`.

## Out of scope
- Low-level OS driver bindings (`T991`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.10.
- Depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, P21 virtual memory `T921`/`T922`, `T956`, and `T989`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T990/build` and `python tools/axtest.py --compiler build-snap-T990/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-10 22:30:00 created by architect (ADR-0040 revision: Epic E22.10 UnifiedBuffer domain handoff & HostImport implementation)
