---
id: T957
title: E22.2 Device memory ownership, explicit transfers, address spaces & in-flight lifetime conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T956]
priority: 227
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_2_device_memory_ownership]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/requirements/OWNER.md, 0120, 0139, 0162, tasks/0299, tasks/0459, tasks/0468, tasks/0470, tasks/0626]
covers: [REQ-OWNER-009, REQ-OPT-347, REQ-GPU-001, REQ-GPU-002, REQ-GPU-004, REQ-GPU-015, REQ-GPU-016, REQ-GPU-017, REQ-GPU-018, REQ-GPU-019, REQ-GPU-020, REQ-GPU-021, REQ-GPU-022, REQ-GPU-029, REQ-GPU-030, REQ-GPU-031, REQ-GPU-033, REQ-GPU-034, REQ-GPU-035, REQ-GPU-036, REQ-GPU-038, REQ-GPU-039, REQ-GPU-040, REQ-GPU-041, REQ-GPU-042, REQ-GPU-043, REQ-GPU-048, REQ-GPU-049, REQ-GPU-050, REQ-GPU-051, REQ-GPU-057, REQ-GPU-059, REQ-GPU-060, REQ-GPU-061, REQ-GPU-063]
---
# T957 — E22.2 Device memory ownership, explicit transfers, address spaces & in-flight lifetime conformance suite

## Goal
Certify E22.2 exit criteria with an end-to-end conformance suite covering GPU address spaces, unified CPU/GPU ownership and capability rules (`AGPU-20`, `AGPU-57..59`), explicit host↔device and multi-GPU transfers (`AGPU-21`, `ATENSOR-29`, `APAR-63-64`), and in-flight `InFlight<B>` lifetime safety (`AGPU-23`, `AGPU-33`).

## Scope
- Create `tests/conformance/p22/e22_2_device_memory_ownership` covering all positive and negative rules in `spec/SPEC-131-device-memory-cross-device-ownership.md`.
- Verify that `DeviceBuffer<T>`, `DeviceView<T>`, and `DeviceMutView<T>` obey the exact same ownership, non-aliasing, and deterministic `Drop` rules as CPU `Vec<T>`/`view<T>`/`mut_view<T>` without introducing a second ownership model (`AGPU-20`, `AGPU-50`).
- Verify negative compile-time rejection of: passing host views/slices directly to `@kernel` parameters expecting device memory (`AGPU-21`), dereferencing device pointers on host, dereferencing host pointers in `@kernel`, dropping or relocating a `DeviceBuffer` while a `DeviceView` is live, concurrent host/device write races on host-accessible memory across every mock adapter, and unauthorized cross-GPU peer access (`APAR-63-64`).
- Verify positive conformance for `ShardedDeviceBuffer<T>`, `peer_copy_async`, and multi-GPU `all_reduce` / `all_gather` / `broadcast` collective synchronization.
- Verify `TransferStats` accounting across transfer operations: `upload`/`download` report exact byte transfers; by-value transitions report 0 bytes copied; ReBAR writes count as `bytes_written_over_bus`.
- Verify LIR inspection (`--emit=lir`) preserves non-zero GPU address spaces (`Device`, `Shared`, `Constant`, `Local`, `Private`) and `domain = Gpu` (`0162 §32-33`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p22/e22_2_device_memory_ownership` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Negative race rejection cases pass against all mock adapter types (`DiscretePool`, `UnifiedSystemPool`, `CoherentMultiPoolNuma`, `ReBarHostVisible`).
- [ ] `InFlight<B>` ownership return, blocking drop, and across-await safety verified with 0 leaks.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T957-report.md` with exact `## Files changed`.

## Out of scope
- Multi-backend hardware driver conformance (moved to `T965`, `T970`, `T992`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, and `T956`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T957/build` and `python tools/axtest.py --compiler build-snap-T957/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: generalized negative race testing across all mock adapters, InFlight conformance, REQ-OWNER-009)
