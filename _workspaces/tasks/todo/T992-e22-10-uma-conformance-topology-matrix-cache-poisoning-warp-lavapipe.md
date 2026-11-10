---
id: T992
title: E22.10 UMA conformance: 4-topology test matrix, simulated non-coherent cache poisoning & WARP/Lavapipe CI
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T957, T965, T970, T991]
priority: 262
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_10_uma_conformance]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-139-unified-memory-architecture.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/requirements/OWNER.md]
covers: [REQ-OWNER-009, REQ-OPT-347]
---
# T992 — E22.10 UMA conformance: 4-topology test matrix, simulated non-coherent cache poisoning & WARP/Lavapipe CI

## Goal
Certify the E22.10 exit criteria with a comprehensive conformance test suite covering the 4 memory topologies (`DiscretePool`, `UnifiedSystemPool`, `CoherentMultiPoolNuma`, `ReBarHostVisible`), simulated non-coherent cache poisoning, software ICD execution (WARP/Lavapipe), and OS memory pressure handling.

## Scope
- Create `tests/conformance/p22/e22_10_uma_conformance`:
  - 4-Topology conformance matrix: execute vector addition, matrix multiply, and buffer handoffs across all 4 topologies (`DiscretePool`, `UnifiedSystemPool`, `CoherentMultiPoolNuma`, `ReBarHostVisible`), asserting identical numerical output buffers.
  - Value-preserving copy elision verification: assert that `upload`/`download` report `bytes_copied == len * size_of::<T>()`; assert that `UnifiedBuffer` domain transitions, by-value `.into_device(self)`, and by-value `.to(device)` report `bytes_copied == 0`.
  - Texture tiling blit verification: assert that uploading to 2D/3D textures performs layout conversion blits and does not claim 0-byte copies.
  - Simulated non-coherent cache poisoning test: configure CPU fallback to poison un-invalidated GPU-written cache lines; verify that missing cache invalidate triggers `MOCK_STALE_CACHE_READ`, and that correct invalidation succeeds with clean data.
  - Software ICD execution: run D3D12 test cases against Microsoft WARP (`d3d10warp.dll`) on Windows and Vulkan test cases against Mesa Lavapipe (`lvp_icd.json`) on Linux in headless CI without physical GPUs.
  - Host import conformance: verify page-aligned `VirtualRegion` and `Mmap` imports; verify rejection of `MmapCow` with `GpuError.HostImportUnsupported`; verify rejection of misaligned imports with `GpuError.HostImportMisaligned`.
  - Memory budget & OS pressure conformance: verify that `Advisory` policy reports `Warning`/`Critical` under pressure without crashing; verify that `StrictBudget` returns `GpuError.OutOfDeviceMemory`.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p22/e22_10_uma_conformance` pass in `--interp` and native modes with `0 WEAK-NATIVE` and bit-identical numerical results across all 4 memory topologies.
- [ ] Simulated non-coherent cache poisoning correctly detects missing invalidate calls (`MOCK_STALE_CACHE_READ`).
- [ ] Software ICD execution (WARP on Windows, Lavapipe on Linux) runs green in headless CI.
- [ ] Host memory import correctly validates alignment, PlainData bounds, and rejects `MmapCow`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T992-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or stdlib modifications; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), closes Epic E22.10.
- Depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, `T957`, `T965`, `T970`, and `T991`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T992/build` and `python tools/axtest.py --compiler build-snap-T992/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-10 22:30:00 created by architect (ADR-0040 revision: Epic E22.10 UMA 4-topology conformance, cache poisoning, WARP/Lavapipe CI)
