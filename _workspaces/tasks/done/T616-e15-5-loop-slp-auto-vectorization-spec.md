---
id: T616
title: E15.5 — Canonical loop & SLP auto-vectorization specification (SPEC-74)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215, T463, T609]
priority: 110
status: done
attempts: 1
paths: [spec/SPEC-74-auto-vectorization.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-42-simd-vectors.md, spec/SPEC-72-loops-scev-bce.md, 0095, 0162, tasks/0402, tasks/0403, tasks/0406, tasks/0407]
covers: [REQ-OPT-013, REQ-OPT-148, REQ-OPT-149, REQ-OPT-150, REQ-OPT-151, REQ-OPT-152, REQ-OPT-153, REQ-OPT-154, REQ-OPT-191]
started: 2026-11-03 13:50:42
finished: 2026-11-03 14:05:59
---
# T616 — E15.5 — Canonical loop & SLP auto-vectorization specification (SPEC-74)

## Goal
Consolidate the canonical specification for loop auto-vectorization, Superword-Level Parallelism (`SLP`) straight-line vectorization, capability-disjoint memory dependence proofs, floating-point/reduction legality, and scalar epilogue fallback into `spec/SPEC-74-auto-vectorization.md` (`AXS-VEC-*` rule IDs).

## Scope
- Write `spec/SPEC-74-auto-vectorization.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-VEC-NNN` rules.
- Specify that auto-vectorization operates before LIR lowering without requiring mandatory source annotations (`0162 §31`, `REQ-OPT-013`) and preserves exact scalar observable semantics (`REQ-OPT-191`).
- Specify memory-dependence legality (`REQ-OPT-148..150`): how verified disjoint capabilities (`mut_view<[T]>` vs `view<[T]>`) and disjoint `SCEV` ranges establish zero loop-carried dependence without runtime alias checks, while `Unknown` aliasing is never assumed `NoAlias`.
- Specify hard barriers for atomics (`REQ-OPT-151`), `volatile` (`REQ-OPT-152`), strict IEEE-754 floating-point ordering vs explicit associative reductions (`REQ-OPT-153`, `REQ-OPT-154`), and checked-arithmetic trap preservation.
- Specify target vector-width cost modeling (`SSE2` 128-bit baseline vs `AVX2` 256-bit under `@target_feature` / target profile), straight-line `SLP` pack trees, and peel/epilogue remainder loops.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-74-auto-vectorization.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-VEC-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T616-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of loop and SLP auto-vectorization (`T617`–`T618`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`); depends on P12 gate `T312` (`ROADMAP.md` §3/§4: E15.5 auto-vectorization requires P12 numeric/float/SIMD types and backend).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:42:00 created by T215 (P15 phase planning)
- 2026-11-03 13:50:42 started (attempt 1) 
- 2026-11-03 14:05:59 accepted by QA -> done
