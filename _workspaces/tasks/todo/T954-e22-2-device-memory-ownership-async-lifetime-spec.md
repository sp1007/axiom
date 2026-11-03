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
spec: [spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/SPEC-51-raw-memory-volatile-mmio-layout.md, 0120, 0139, 0162, tasks/0299, tasks/0459, tasks/0468, tasks/0470, tasks/0626]
covers: [REQ-GPU-001, REQ-GPU-002, REQ-GPU-004, REQ-GPU-007, REQ-GPU-015, REQ-GPU-016, REQ-GPU-017, REQ-GPU-018, REQ-GPU-019, REQ-GPU-020, REQ-GPU-021, REQ-GPU-022, REQ-GPU-029, REQ-GPU-030, REQ-GPU-031, REQ-GPU-033, REQ-GPU-034, REQ-GPU-035, REQ-GPU-036, REQ-GPU-038, REQ-GPU-039, REQ-GPU-040, REQ-GPU-041, REQ-GPU-042, REQ-GPU-043, REQ-GPU-044, REQ-GPU-048, REQ-GPU-049, REQ-GPU-050, REQ-GPU-051, REQ-GPU-057, REQ-GPU-059, REQ-GPU-060, REQ-GPU-061, REQ-GPU-063]
---
# T954 — E22.2 Canonical device memory spaces, DeviceBuffer/DeviceView ownership & async event lifetime specification (SPEC-131)

## Goal
Consolidate the canonical specification for Axiom's GPU/accelerator storage and address spaces, unified CPU/GPU ownership and capability model, `DeviceBuffer<T>` / `DeviceView<T>` / `DeviceMutView<T>`, explicit host↔device and peer-device transfers, and in-flight `GpuEvent` resource lifetime retention into `spec/SPEC-131-device-memory-cross-device-ownership.md` (`AXS-GMEM-*` rule IDs).

## Scope
- Write `spec/SPEC-131-device-memory-cross-device-ownership.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GMEM-NNN` rules (`0120 §265-274`, `0139 §XX.6-XX.18, §XX.31-XX.44`, `0162 §32-33`, `tasks/0299 §7-23`, `tasks/0626 §6-19`).
- Specify semantic storage and address spaces (`Host = 0`, `Device = 1`, `Shared = 2`, `Constant = 3`, `Local = 4`, `Private = 5`, `External = 6` matching `SPEC-04 AXS-EXT-020/042/051` and `SPEC-51`), requiring backends and LIR to preserve non-generic address spaces (`0162 §32-33`) and forbidding implicit host↔device pointer or view conversions (`AGPU-21`, `0139 §XX.7-8`).
- Specify the unified ownership and capability contract across domains (`AGPU-20`, `AGPU-57..59`): `DeviceBuffer<T>` owns device storage without runtime object headers (`AGPU-24`), `DeviceView<T>` (`view<T @device>`) and `DeviceMutView<T>` (`mut_view<T @device>`) are non-owning capabilities obeying standard exclusive-mutable aliasing and disjointness rules (`0139 §XX.9-11`), and `SharedArray<T, N>` cannot escape workgroup scope (`tasks/0626 §17`).
- Specify explicit host↔device, device↔device, and multi-GPU peer transfer contracts (`upload`, `download`, `upload_async`, `download_async`, `device_copy`, `peer_copy`, and tensor `.to(device)` / `.to_async(device)` per `ATENSOR-29`, `APAR-63-64`), plus `UnifiedBuffer<T>` explicit cross-domain synchronization (`0139 §XX.12-14`).
- Specify in-flight asynchronous operation lifetime and `Drop`/relocation safety (`AGPU-23`, `AGPU-33`, `0139 §XX.15-17, §XX.31`): `GpuEvent` establishes explicit resource lifetime dependencies and `synchronizes-with` happens-before edges so a `DeviceBuffer<T>` or pinned host buffer cannot be dropped, invalidated, or relocated while an in-flight kernel or transfer accesses it.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-131-device-memory-cross-device-ownership.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-GMEM-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T954-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and stdlib implementation of device memory ownership and transfers (`T955`–`T956`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T954/build` and `python tools/axtest.py --compiler build-snap-T954/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
