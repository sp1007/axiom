---
id: T955
title: E22.2 Address-space typing, cross-domain capability isolation & in-flight GpuEvent lifetime verifier
phase: P22-gpu-heterogeneous-computing
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T952, T954]
priority: 225
status: todo
attempts: 0
paths: [compiler/semantics/gpu_memory, compiler/mir/gpu_transfer, tests/ui/gpu_memory_ownership]
locks: [compiler/semantics/own.ax, compiler/semantics/cap.ax, compiler/mir/verifier.ax, compiler/lir/lir.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, 0120, 0139, 0162, tasks/0299, tasks/0626]
covers: [REQ-GPU-001, REQ-GPU-002, REQ-GPU-004, REQ-GPU-015, REQ-GPU-016, REQ-GPU-017, REQ-GPU-018, REQ-GPU-019, REQ-GPU-020, REQ-GPU-021, REQ-GPU-022, REQ-GPU-029, REQ-GPU-030, REQ-GPU-031, REQ-GPU-033, REQ-GPU-038, REQ-GPU-039, REQ-GPU-040, REQ-GPU-041, REQ-GPU-042, REQ-GPU-043, REQ-GPU-048, REQ-GPU-049, REQ-GPU-050, REQ-GPU-051, REQ-GPU-054, REQ-GPU-055, REQ-GPU-057, REQ-GPU-059, REQ-GPU-060]
---
# T955 — E22.2 Address-space typing, cross-domain capability isolation & in-flight GpuEvent lifetime verifier

## Goal
Implement non-zero GPU address-space typing, cross-domain capability isolation, disjoint `DeviceMutView` verification, and in-flight `GpuEvent` resource lifetime checking in `compiler/` per `spec/SPEC-131-device-memory-cross-device-ownership.md`.

## Scope
- Implement storage/address-space propagation (`Host = 0`, `Device = 1`, `Shared = 2`, `Constant = 3`, `Local = 4`, `Private = 5`, `External = 6`) in `compiler/semantics/gpu_memory`, `compiler/mir/gpu_transfer`, and `compiler/lir/lir.ax` (`SPEC-04 AXS-EXT-020/042/051`, `0162 §32-33`), ensuring GPU backends never collapse device address spaces into generic address space `0`.
- Enforce cross-domain capability isolation in `compiler/semantics/own.ax` and `compiler/semantics/cap.ax`: reject implicit host-to-device or device-to-host conversions (`AGPU-21`), reject host dereferencing of `Device` pointers/views and kernel dereferencing of `Host` pointers/views, require `unsafe` for `CastKind.PtrAddrSpace` (`0139 §XX.8, §XX.44`), and forbid escaping `Shared` workgroup storage (`tasks/0626 §17`).
- Enforce exclusive `DeviceMutView<T>` aliasing and disjointness across kernel launch arguments (`0139 §XX.11`), and forbid aliasing `Atomic` device storage through ordinary mutable views (`0139 §XX.23, §XX.41`).
- Enforce in-flight `GpuEvent` resource lifetime retention (`AGPU-23`, `AGPU-33`, `0139 §XX.16-17, §XX.31, §XX.41`): reject `drop(buffer)` or buffer relocation while an un-awaited `GpuEvent` or live `DeviceView`/`DeviceMutView` derived from `buffer` remains active.
- Enforce UMA CPU↔GPU race freedom on `UnifiedBuffer<T>` (ADR-0040 §5): reject a live host `mut_view<T>` while an un-awaited `GpuEvent` accesses the same buffer and vice versa (`AX_GPU_UMA_HOST_DEVICE_RACE`), reject `munmap` / drop of a mapping imported via `UnifiedBuffer.from_mmap` while the imported buffer lives, and accept concurrent `shared_read_views()` (host `view<T>` + `DeviceView<T>`).
- Add positive and negative UI diagnostic tests in `tests/ui/gpu_memory_ownership`.

## Acceptance
- [ ] UI tests in `tests/ui/gpu_memory_ownership` verify compile-time rejection of implicit host↔device transfers, host pointer dereferences in `@kernel`, overlapping `DeviceMutView` kernel arguments, `Shared` memory escape, and dropping/relocating a `DeviceBuffer` before an in-flight `GpuEvent` completes, plus UMA host/device write races on `UnifiedBuffer<T>` (`AX_GPU_UMA_HOST_DEVICE_RACE`) and acceptance of concurrent `shared_read_views()`.
- [ ] LIR dumps (`inspect --emit=lir`) preserve explicit GPU execution domain and non-zero address spaces on all device memory operations (`0162 §32-33`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T955-report.md` with exact `## Files changed`.

## Out of scope
- Standard library `std.gpu.mem` / `std.gpu.transfer` implementation (`T956`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T955/build` and `python tools/axtest.py --compiler build-snap-T955/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
