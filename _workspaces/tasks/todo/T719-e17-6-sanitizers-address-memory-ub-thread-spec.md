---
id: T719
title: E17.6 Canonical dynamic sanitizers (Address/Memory/Bounds/UB/Thread) & runtime verification specification (SPEC-97)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316, T711]
priority: 190
status: todo
attempts: 0
paths: [spec/SPEC-97-sanitizers-runtime-verification.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-95-debugger-contract-symbolication.md, 0147, tasks/0599, tasks/0694, tasks/0733]
covers: [REQ-DBG-116, REQ-DBG-120]
---
# T719 — E17.6 Canonical dynamic sanitizers (Address/Memory/Bounds/UB/Thread) & runtime verification specification (SPEC-97)

## Goal
Consolidate the canonical specification for Axiom dynamic sanitizers (--sanitize=address|memory|ub|thread|bounds|all) and runtime verification into spec/SPEC-97-sanitizers-runtime-verification.md (AXS-SAN-* rules).

## Scope
- Write `spec/SPEC-97-sanitizers-runtime-verification.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-SAN-NNN` rules.
- Specify the sanitizer semantic boundary (`0599 §1–5`, `tasks/0733 §480.1`, `ADEBUG-86`–`ADEBUG-87`): sanitizers never alter valid program semantics, never replace static ownership/capability verification, and incur zero cost when disabled.
- Specify Address, Bounds & Provenance Sanitizer (`--sanitize=address,bounds`, `0599 §6–12, §18–19`, `0733 §480.2–7, §480.13–14`): shadow memory poisoning, heap/stack/global redzones, quarantine delay queues with alloc/free stack traces, use-after-free, double-free, invalid free, raw-pointer provenance tag validation, and FFI buffer boundary verification.
- Specify Uninitialized-Memory Sanitizer (`--sanitize=memory`, `0599 §13–14`, `0733 §480.8–9`): shadow bit-level initialization tracking across `MaybeUninit<T>`, raw heap allocations, and FFI out-parameters.
- Specify Undefined-Behavior & Integer Sanitizer (`--sanitize=ub`, `0599 §15–17`, `0733 §480.10–12`): unchecked arithmetic overflow in `unsafe`, invalid shift distances, division/remainder by zero, misaligned/null raw pointer dereference, and invalid `bool`/enum discriminant bit patterns.
- Specify Concurrency & Data-Race Sanitizer (`--sanitize=thread`, `0733 §480.15–19`): per-thread vector clocks, shadow memory access tracking for `unsafe` shared state, lock-order acquisition graph cycle detection, and structured source-mapped diagnostic reports.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-97-sanitizers-runtime-verification.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-SAN-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T719-report.md` with exact `## Files changed`.

## Out of scope
- Compiler sanitizer instrumentation pass and runtime library (`T720`, `T721`, `T722`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
