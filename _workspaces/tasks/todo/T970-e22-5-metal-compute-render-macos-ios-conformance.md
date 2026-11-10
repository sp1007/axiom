---
id: T970
title: E22.5 Metal compute & render pipeline cross-platform (macOS & iOS) conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T699, T969]
priority: 240
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_5_metal_backend]
locks: [tests/conformance/p22/mod.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-134-apple-metal-msl-backend.md, spec/requirements/OWNER.md, 0096, 0139, tasks/0846]
covers: [REQ-OWNER-009, REQ-GPU-007, REQ-GPU-065]
---
# T970 — E22.5 Metal compute & render pipeline cross-platform (macOS & iOS) conformance suite

## Goal
Implement the end-to-end conformance test suite for Apple Metal compute execution on macOS and iOS, verifying that Axiom kernels compiled to MSL execute with bit-for-bit parity against the reference software oracle.

## Scope
- Implement the test suite in `tests/conformance/p22/e22_5_metal_backend`:
  - 1D, 2D, and 3D grid dispatch: vector add, matrix multiply, 2D stencil convolution, prefix sum.
  - Workgroup memory and synchronization: shared array reduction and barrier coherence.
  - Half-precision (`f16`) compute validation on Apple Silicon GPUs.
  - Generational `DeviceId` validation, device lost handling, and command queue recovery.
  - Zero-copy `UnifiedBuffer` round-trip testing on Apple Silicon hardware (with fallback validation under simulator).
  - Verify UMA conformance per ADR-0040: zero-copy transfer elision on Apple Silicon, `HostImport` 16 KiB alignment verification, and memory pressure callbacks under simulated memory pressure.
- Implement automated test runners for macOS native and iOS Simulator environments, capturing output buffers and comparing checksums against host CPU results.
- Implement differential verification comparing results produced by the Metal backend against the SPIR-V/Vulkan and D3D12 backends.

## Acceptance
- [ ] All tests in `tests/conformance/p22/e22_5_metal_backend` pass with identical output buffers to the CPU reference oracle.
- [ ] UMA zero-copy transfer elision and `HostImport` conformance pass on Apple Silicon hardware and on iOS Simulator with bit-identical results.
- [ ] Zero capability leaks or memory crashes across repeated dispatch and buffer re-allocation cycles.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T970-report.md` with exact `## Files changed`.

## Out of scope
- Live shader hot-reload (`E22.8`, `T983`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), closes Epic E22.5.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T970/build` and `python tools/axtest.py --compiler build-snap-T970/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Metal expansion)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: added Metal UMA & HostImport conformance, REQ-OWNER-009)
