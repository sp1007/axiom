---
id: T760
title: E18.3 — Canonical parallel compilation & deterministic DAG scheduling specification (SPEC-23)
phase: P18-compiler-architecture-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T756]
priority: 710
status: done
attempts: 1
paths: [spec/SPEC-23-parallel-compilation.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-22-incremental-compilation.md, tasks/0473, tasks/0528, tasks/0530, tasks/0593, tasks/0789, tasks/0790]
covers: [REQ-DRV-018, REQ-CORE-2669, REQ-CORE-2670, REQ-CORE-2671, REQ-CORE-2672, REQ-CORE-2673, REQ-CORE-2674, REQ-CORE-2675, REQ-CORE-2676, REQ-CORE-2677, REQ-CORE-2678, REQ-CORE-2679, REQ-CORE-2680, REQ-CORE-2681, REQ-CORE-2682, REQ-CORE-2683, REQ-CORE-2684, REQ-CORE-2685, REQ-CORE-2686, REQ-CORE-2687, REQ-CORE-2688, REQ-CORE-2689, REQ-CORE-2690, REQ-CORE-2691, REQ-CORE-2692, REQ-CORE-2693, REQ-CORE-2694, REQ-CORE-2695, REQ-CORE-2696, REQ-CORE-2697, REQ-CORE-2698, REQ-CORE-2699, REQ-CORE-2700, REQ-CORE-2701, REQ-CORE-2702, REQ-CORE-2703, REQ-CORE-2704, REQ-CORE-2705, REQ-CORE-2706, REQ-CORE-2707, REQ-CORE-2708, REQ-CORE-2709, REQ-CORE-2710, REQ-CORE-2711, REQ-CORE-3125, REQ-CORE-3126]
started: 2026-11-03 12:41:32
finished: 2026-11-03 13:00:37
---
# T760 — E18.3 — Canonical parallel compilation & deterministic DAG scheduling specification (SPEC-23)

## Goal
Consolidate the canonical specification for Axiom's parallel compilation architecture, work-stealing query/action DAG scheduling, thread-count-independent ID assignment, and deterministic diagnostic/artifact merging into `spec/SPEC-23-parallel-compilation.md` (`AXS-PAR-*` rule IDs).

## Scope
- Write `spec/SPEC-23-parallel-compilation.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-PAR-NNN` rules.
- Specify the fundamental parallel invariant (`tasks/0528`, `tasks/0530`, `tasks/0790`): parallelism changes physical execution order only, never semantic IDs, diagnostics, symbol tables, or output bytes (`--jobs 1` == `--jobs N`).
- Specify module-scoped / content-addressed ID allocation and sharded string/type interning so concurrent workers never race on sequential global counters.
- Specify in-flight query deduplication (single-flight latch with cross-worker cycle detection on the wait-for graph) and deterministic post-join diagnostic/object merging (`tasks/0789`, `tasks/0790`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-23-parallel-compilation.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-PAR-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T760-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of parallel query scheduling and codegen (`T761`–`T762`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:58:15 created by T218 (P18 phase planning)
- 2026-11-03 12:41:32 started (attempt 1) 
- 2026-11-03 13:00:37 accepted by QA -> done
