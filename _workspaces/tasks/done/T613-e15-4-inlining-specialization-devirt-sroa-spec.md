---
id: T613
title: E15.4 — Canonical inlining, specialization, devirtualization & SROA specification (SPEC-73)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215, T600]
priority: 106
status: done
attempts: 1
paths: [spec/SPEC-73-inlining-specialization-devirt.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-70-optir-ssa-memoryssa.md, 0131, 0165, tasks/0366, tasks/0400, tasks/0401, tasks/0551]
covers: [REQ-OPT-002, REQ-OPT-003, REQ-OPT-004, REQ-OPT-005, REQ-OPT-006, REQ-OPT-007, REQ-OPT-009, REQ-OPT-066, REQ-OPT-067, REQ-OPT-068, REQ-OPT-069, REQ-OPT-070, REQ-OPT-071, REQ-OPT-072, REQ-OPT-073, REQ-OPT-074, REQ-OPT-075, REQ-OPT-076, REQ-OPT-077, REQ-OPT-078, REQ-OPT-079, REQ-OPT-080, REQ-OPT-081, REQ-OPT-082, REQ-OPT-083, REQ-OPT-084, REQ-OPT-085, REQ-OPT-086]
started: 2026-11-03 05:12:24
finished: 2026-11-03 05:26:01
---
# T613 — E15.4 — Canonical inlining, specialization, devirtualization & SROA specification (SPEC-73)

## Goal
Consolidate the canonical specification for interprocedural call-graph analysis, function and closure inlining, Scalar Replacement of Aggregates (`SROA`), return-slot construction (`RVO`/`NRVO`), call-site/generic specialization, devirtualization, and tail-call optimization into `spec/SPEC-73-inlining-specialization-devirt.md` (`AXS-INL-*` rule IDs).

## Scope
- Write `spec/SPEC-73-inlining-specialization-devirt.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-INL-NNN` rules.
- Specify interprocedural call-graph SCC analysis, function effect/escape summaries (`tasks/0400`, `REQ-OPT-066..069`), and the separation of inlining legality from cost-model profitability (`tasks/0401`, `REQ-OPT-070..086`).
- Specify `@inline`, `@inline(always)`, and `@inline(never)` semantics (`0131 §73-75`, `REQ-OPT-004..009`, `REQ-OPT-082`, `REQ-OPT-083`), bounded recursive SCC expansion, and preservation of `Drop`, ownership, capability, atomic, and FFI/ABI contracts across inlined boundaries.
- Specify Scalar Replacement of Aggregates (`SROA`), copy/move propagation, return-slot construction (`0152 §74`), closure capture inlining/erasure (`REQ-OPT-084`, `REQ-OPT-085`), call-site constant/closure specialization (`tasks/0551`), proven concrete-target devirtualization of `dyn Trait` / function pointers, and tail-call optimization (`@tailcall` / opportunistic TCO, `REQ-OPT-002`, `REQ-OPT-003`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-73-inlining-specialization-devirt.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-INL-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T613-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of SROA, inlining, specialization, and devirtualization (`T064`, `T614`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:41:00 created by T215 (P15 phase planning)
- 2026-11-03 05:12:24 started (attempt 1) 
- 2026-11-03 05:26:01 accepted by QA -> done
