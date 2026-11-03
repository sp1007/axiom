---
id: T950
title: E22.1 Canonical execution domains, @kernel legality & SIMT synchronization specification (SPEC-130)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316]
priority: 220
status: todo
attempts: 0
paths: [spec/SPEC-130-execution-domains-kernel-model.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, spec/SPEC-30-concurrency.md, spec/SPEC-31-atomics.md, 0096, 0120, 0128, 0139, tasks/0299, tasks/0470, tasks/0626]
covers: [REQ-GPU-003, REQ-GPU-005, REQ-GPU-006, REQ-GPU-007, REQ-GPU-008, REQ-GPU-009, REQ-GPU-010, REQ-GPU-011, REQ-GPU-012, REQ-GPU-013, REQ-GPU-014, REQ-GPU-023, REQ-GPU-024, REQ-GPU-025, REQ-GPU-026, REQ-GPU-027, REQ-GPU-028, REQ-GPU-032, REQ-GPU-037, REQ-GPU-044, REQ-GPU-045, REQ-GPU-046, REQ-GPU-052, REQ-GPU-053, REQ-GPU-056, REQ-GPU-058, REQ-GPU-062]
---
# T950 — E22.1 Canonical execution domains, @kernel legality & SIMT synchronization specification (SPEC-130)

## Goal
Consolidate the canonical specification for Axiom's heterogeneous execution domains, `@kernel`/`@device`/`@host_device` function contracts, transitive kernel call-graph legality, SIMT execution hierarchy, workgroup barrier uniformity, and scoped GPU atomics into `spec/SPEC-130-execution-domains-kernel-model.md` (`AXS-GPU-*` rule IDs).

## Scope
- Write `spec/SPEC-130-execution-domains-kernel-model.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GPU-NNN` rules (`0096 §1-6`, `0120 §265-272`, `0139 §XX.1-XX.28`, `tasks/0299 §1-24`, `tasks/0626 §1-16`).
- Specify `ExecutionDomain` (`Host`, `Device(Gpu | Npu | Dsp | Custom)`) and `FnExecCapability` (`HostOnly`, `DeviceOnly`, `HostDevice`, `KernelEntry`) extending `SPEC-04 AXS-EXT-022/032/040`, ensuring one unified Axiom semantic core across CPU and GPU without a separate kernel sub-language (`AGPU-24`, `AGPU-27`).
- Specify `@kernel`, `@device`, and `@host_device` attribute rules and transitive call-graph legality verification (`AGPU-22`, `AGPU-26`): rejecting host-only I/O (`std.fs`, `std.net`, console `print`), OS syscalls, blocking CPU `Mutex`, implicit host heap allocations (`AGPU-25`), exceptions/unwinding, host-state captures, and target-unsupported recursion or indirect calls with `AX_GPU_*` diagnostics.
- Specify kernel parameter ABI representability (`AGPU-46`, `0139 §XX.24-25`): device views (`DeviceView<T>`, `DeviceMutView<T>`), scalars, SIMD vectors, and plain device-layout structs, plus compile-time generic/comptime kernel specialization re-verification (`AGPU-20`, `0139 §XX.36`).
- Specify SIMT execution hierarchy (`global_id`, `local_id`, `group_id`, `local_size`, `global_size`, `num_groups` distinct from CPU threads, `APAR-31-32`), workgroup collective barrier uniformity (`workgroup.barrier()`, rejecting divergent barriers across lane-dependent branches, `0139 §XX.20-21`), and hierarchical `AtomicScope` (`Thread`, `Workgroup`, `Device`, `System`) orthogonal to `Ordering` (`0128 §63-66`, `AATOM-38`, `SPEC-31`).
- Update `spec/INDEX.md`, `spec/diagnostics.md` (registering `AX_GPU_*` diagnostic codes), and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-130-execution-domains-kernel-model.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-GPU-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T950-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and runtime implementation of `@kernel` legality and SIMT intrinsics (`T951`–`T952`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T950/build` and `python tools/axtest.py --compiler build-snap-T950/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
