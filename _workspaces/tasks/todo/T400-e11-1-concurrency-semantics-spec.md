---
id: T400
title: E11.1 — Canonical concurrency semantics & memory model specification (SPEC-30)
phase: P11-concurrency-async
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T211]
priority: 120
status: todo
attempts: 0
paths: [spec/SPEC-30-concurrency.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0033, 0040, 0079, 0091, 0105, 0126, 0136, tasks/0298, tasks/0488, tasks/0685]
covers: [REQ-CONC-019, REQ-CONC-021, REQ-CONC-025, REQ-CONC-026, REQ-CONC-027, REQ-CONC-028, REQ-CONC-050, REQ-CONC-055, REQ-CONC-067, REQ-CONC-068, REQ-CONC-073, REQ-CONC-082, REQ-CONC-083, REQ-CONC-095, REQ-CONC-101, REQ-CONC-102, REQ-CONC-107, REQ-CONC-109, REQ-CONC-117, REQ-CONC-119, REQ-CONC-120, REQ-CONC-126, REQ-CONC-127, REQ-CONC-128, REQ-CONC-131, REQ-RT-022, REQ-CONC-136, REQ-CONC-137, REQ-CONC-138, REQ-CONC-139, REQ-CONC-140, REQ-CONC-141, REQ-CONC-145, REQ-CONC-156]
---
# T400 — E11.1 — Canonical concurrency semantics & memory model specification (SPEC-30)

## Goal
Consolidate the concurrency and execution-domain design corpus into canonical `spec/SPEC-30-concurrency.md` (`AXS-CONC-*` rule IDs), establishing the unified ownership, capability, `Send`/`Share` auto-trait, data-race freedom, and happens-before memory model that all Phase 11 tasks implement.

## Scope
- Write `spec/SPEC-30-concurrency.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-CONC-NNN` rules.
- Define execution contexts (OS thread, async task, stackful fiber, Future computation, GPU invocation) as distinct from scheduling abstractions (`0126 §1-4`, `tasks/0488 §10-14`).
- Specify `Send` (ownership transfer across execution contexts) and `Share` (concurrent shared read access via `view<T>`) as independent auto-derived marker traits (`Send != Share`), including exact derivation rules for primitives, ADTs, `view<T>`, `mut_view<T>`, raw pointers (`!Send`, `!Share` by default), closures, and explicit `unsafe impl Send/Share` override contracts.
- Specify closure and `spawn` vs `spawn_local` capture rules: `move` ownership transfer, prohibition of non-escaping `view`/`mut_view` in escaping closures, and `Send` obligations.
- Define the compile-time data-race freedom rules (`READ/READ` allowed on `Share`, unsynchronized `READ/WRITE` and `WRITE/WRITE` rejected, disjoint struct field/slice split borrows allowed, mutable globals restricted to `unsafe` or synchronized types) and the happens-before synchronization contract (`spawn`, `join`, lock/unlock, channel send/recv, atomic Acquire/Release/SeqCst).
- Register `AX_CONC_*` diagnostic codes in `spec/diagnostics.md`, concurrency invariants (`INV-CONC-*`) in `spec/invariants.md`, and add `SPEC-30` to `spec/INDEX.md`.

## Acceptance
- [ ] `spec/SPEC-30-concurrency.md` exists with a Vietnamese `## Tóm tắt`, stable `AXS-CONC-NNN` rule IDs, positive/negative Axiom examples using `=` and `.` syntax, and source citations.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` are updated consistently with `SPEC-30`.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T400-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or standard library code changes (handled by `T089`, `T401`–`T403`).
- Editing `docs/` or `bootstrap/axiom0/`.

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T400/build` and `python tools/axtest.py --compiler build-snap-T400/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
