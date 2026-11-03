---
id: T953
title: E22.1 Execution domains, @kernel transitive legality, barrier uniformity & oracle SIMT conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T952]
priority: 223
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_1_execution_domains_kernel]
spec: [spec/SPEC-130-execution-domains-kernel-model.md, 0096, 0120, 0128, 0139, tasks/0299, tasks/0470, tasks/0626]
covers: [REQ-GPU-003, REQ-GPU-005, REQ-GPU-006, REQ-GPU-008, REQ-GPU-009, REQ-GPU-010, REQ-GPU-011, REQ-GPU-012, REQ-GPU-013, REQ-GPU-014, REQ-GPU-023, REQ-GPU-024, REQ-GPU-025, REQ-GPU-026, REQ-GPU-027, REQ-GPU-028, REQ-GPU-037, REQ-GPU-044, REQ-GPU-045, REQ-GPU-046, REQ-GPU-056, REQ-GPU-058, REQ-GPU-062]
---
# T953 — E22.1 Execution domains, @kernel transitive legality, barrier uniformity & oracle SIMT conformance suite

## Goal
Certify E22.1 exit criteria with a comprehensive conformance suite covering execution domains (`@kernel`, `@device`, `@host_device`), transitive call-graph legality, kernel parameter ABI rules, workgroup barrier uniformity, scoped GPU atomics (`AATOM-38`), and oracle SIMT grid execution.

## Scope
- Create `tests/conformance/p22/e22_1_execution_domains_kernel` with positive and negative conformance tests covering every `AXS-GPU-*` rule of `spec/SPEC-130-execution-domains-kernel-model.md`.
- Verify transitive rejection of host-only calls (`File`, `Socket`, OS syscalls, `Mutex`, host heap allocation, host global/capture references) through multi-hop helper chains (`AGPU-22`, `AGPU-26`).
- Verify dual-domain `@host_device` functions executing identically on CPU and inside `@kernel` dispatches (`0139 §XX.5`), plus generic/comptime kernel specialization re-verification (`AGPU-20`).
- Verify SIMT workgroup barrier synchronization, compile-time and oracle rejection of divergent barriers (`0139 §XX.21`), and hierarchical `AtomicScope` (`Workgroup`, `Device`, `System`) with `Relaxed`/`Acquire`/`Release`/`AcqRel`/`SeqCst` orderings (`0128 §63-66`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p22/e22_1_execution_domains_kernel` pass with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T953-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or stdlib changes; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T953/build` and `python tools/axtest.py --compiler build-snap-T953/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
