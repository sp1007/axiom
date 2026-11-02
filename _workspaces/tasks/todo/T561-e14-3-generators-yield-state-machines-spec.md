---
id: T561
title: E14.3 — Canonical generators, yield suspension, iterator state machines & MIR verification specification (SPEC-62)
phase: P14-comptime-2-0-reflection-genera
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T214]
priority: 181
status: todo
attempts: 0
paths: [spec/SPEC-62-generators.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/SPEC-12-drop.md, tasks/0512, tasks/0539]
covers: [REQ-CORE-2989, REQ-CORE-2990, REQ-CORE-2991, REQ-CORE-2992, REQ-CORE-2993, REQ-CORE-2994, REQ-CORE-2995, REQ-CORE-2996, REQ-CORE-2997, REQ-CORE-2998]
---
# T561 — E14.3 — Canonical generators, yield suspension, iterator state machines & MIR verification specification (SPEC-62)

## Goal
Define the canonical language and MIR semantics for synchronous generators (`gen fn`, `yield`), zero-heap iterator state machines, capability/ownership rules across `yield` points, and per-state `Drop` cleanup in `spec/SPEC-62-generators.md` (`AXS-GEN-*` rule IDs).

## Scope
- Write `spec/SPEC-62-generators.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GEN-NNN` rules.
- Specify `gen fn name(...) -> Yield<T>` (or `impl Iterator<Item = T>`) and `yield expr` evaluation order: generator creation is lazy and does not execute the body until `next(mut_view(g))` is called (`AGEN-20..28`).
- Specify generator ownership and capability rules (`AGEN-29..65`, `AMIR-20..55`): generators are non-`Copy` by default, locals live across a `YieldPointId` are captured in the generated state-machine struct, ephemeral capabilities and self-referential borrows into generator locals cannot cross `yield` (`AX_GEN_VIEW_ACROSS_YIELD`), and yielded views require valid provenance from input parameters.
- Specify terminal completion (`None` on subsequent calls after return or panic) and deterministic per-state `Drop` cleanup when a suspended generator is dropped early (`AGEN-43..49`, `AMIR-38..48`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-62-generators.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-GEN-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T561-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or library implementation (handled by `T562`–`T564`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:22:30 created by T214 (P14 phase planning)
