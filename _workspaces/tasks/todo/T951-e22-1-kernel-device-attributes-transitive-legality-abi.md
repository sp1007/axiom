---
id: T951
title: E22.1 @kernel/@device attributes, transitive execution-domain legality & kernel ABI checker
phase: P22-gpu-heterogeneous-computing
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T950]
priority: 221
status: todo
attempts: 0
paths: [compiler/hir/gpu_domain, compiler/semantics/gpu_legality, tests/ui/gpu_legality]
locks: [compiler/hir/attr.ax, compiler/semantics/typeck.ax, compiler/diag/codes.ax]
spec: [spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-04-core-extensibility.md, 0096, 0120, 0139, tasks/0299, tasks/0626]
covers: [REQ-GPU-003, REQ-GPU-006, REQ-GPU-008, REQ-GPU-009, REQ-GPU-010, REQ-GPU-011, REQ-GPU-012, REQ-GPU-013, REQ-GPU-014, REQ-GPU-024, REQ-GPU-025, REQ-GPU-026, REQ-GPU-027, REQ-GPU-028, REQ-GPU-032, REQ-GPU-037, REQ-GPU-046, REQ-GPU-052, REQ-GPU-053, REQ-GPU-056, REQ-GPU-058]
---
# T951 — E22.1 @kernel/@device attributes, transitive execution-domain legality & kernel ABI checker

## Goal
Implement `@kernel`, `@device`, and `@host_device` attribute lowering, transitive execution-domain call-graph legality checking, and kernel parameter ABI representability verification in `compiler/` per `spec/SPEC-130-execution-domains-kernel-model.md`.

## Scope
- Implement `@kernel`, `@device`, and `@host_device` attribute lowering in `compiler/hir/gpu_domain` and `compiler/hir/attr.ax`, populating `ExecutionDomain`, `FnExecCapability`, and `CallConv.GpuKernel` on function signatures (`SPEC-04 AXS-EXT-022/032/091`).
- Implement transitive call-graph domain legality checking in `compiler/semantics/gpu_legality`: verify that every `@kernel` and `@device` function transitively calls only `DeviceOnly` or `HostDevice` functions, rejecting host-only APIs (`std.fs`, `std.net`, OS syscalls, blocking `Mutex`, host heap allocations, and unannotated host helpers) with `AX_GPU_*` diagnostics (`AGPU-22`, `AGPU-26`, `0139 §XX.4-5`).
- Implement kernel parameter and capture ABI representability checking (`AGPU-46`, `0139 §XX.24-28, §XX.32`): reject host `view`/`mut_view`/raw pointers, non-device trait objects/closures, host-owned handle types, and target-forbidden recursion in `@kernel` signatures and bodies.
- Ensure generic and comptime-specialized `@kernel` instantiations re-run full type, ownership, capability, and domain-legality verification (`AGPU-20`, `0139 §XX.36`, `tasks/0626 §30`).
- Add positive and negative UI diagnostic tests in `tests/ui/gpu_legality`.

## Acceptance
- [ ] UI tests in `tests/ui/gpu_legality` verify that `@kernel` functions calling host-only helpers (directly or transitively), accepting non-device-representable parameters, or performing forbidden host operations are rejected at compile time with exact `AX_GPU_*` diagnostics, while valid `@kernel`/`@device`/`@host_device` call graphs compile cleanly.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T951-report.md` with exact `## Files changed`.

## Out of scope
- Kernel MIR intrinsics, barrier uniformity verifier, and oracle SIMT grid execution (`T952`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T951/build` and `python tools/axtest.py --compiler build-snap-T951/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
