---
id: T064
title: E15.4 — Optimizer ladder 2: copy/move propagation, SROA, return-slot construction & call-graph inlining
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215, T603, T607, T610, T613]
priority: 107
status: todo
attempts: 0
paths: [compiler/opt, tests/opt2]
spec: [spec/SPEC-73-inlining-specialization-devirt.md, 0165, 0226, tasks/0366, tasks/0399, tasks/0401, tasks/0551]
covers: [REQ-TYP-001, REQ-TYP-002, REQ-TYP-003, REQ-TYP-004, REQ-TYP-005, REQ-TYP-006, REQ-OPT-114, REQ-OPT-115, REQ-OPT-116, REQ-OPT-117, REQ-OPT-118, REQ-OPT-119, REQ-OPT-120, REQ-OPT-121, REQ-OPT-122, REQ-OPT-123, REQ-OPT-124, REQ-OPT-315, REQ-OPT-316, REQ-OPT-317, REQ-OPT-318]
---
# T064 — E15.4 — Optimizer ladder 2: copy/move propagation, SROA, return-slot construction & call-graph inlining

## Goal
Implement ownership- and capability-aware copy/move propagation, Scalar Replacement of Aggregates (`SROA`), caller-allocated return-slot construction (`RVO`/`NRVO`), and bottom-up SCC call-graph inlining in `compiler/opt` per `spec/SPEC-73-inlining-specialization-devirt.md`.

## Scope
- Implement copy and move propagation in `compiler/opt`, eliding intermediate aggregate copies/moves while preserving `Drop` flags, capability boundaries, and address-taken barriers (`REQ-OPT-114..124`).
- Implement Scalar Replacement of Aggregates (`SROA`) decomposing non-escaping structs, tuples, `Option`/`Result` payloads, and closure environments into scalar SSA values.
- Implement return-slot construction (`RVO`/`NRVO`, `0152 §74`) eliminating temporary aggregate copies on function return.
- Implement bottom-up call-graph SCC inlining honoring `@inline`, `@inline(always)`, and `@inline(never)` (`REQ-OPT-315..318`), bounded recursion depth, and post-inline `SROA`/scalar cleanup.

## Acceptance
- [ ] Differential run and dump tests in `tests/opt2` verify copy/move propagation, `SROA`, return-slot construction, and `@inline`/`@inline(always)`/`@inline(never)` inlining with exact `--interp` and native `-O0`/`-O1`/`-O2` agreement; perf numbers recorded via `tools/perf.py`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T064-report.md` with exact `## Files changed`.

## Out of scope
- Interprocedural call-site specialization, `dyn Trait` devirtualization, and tail-call optimization (`T614`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Roadmap epic E15.4 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; refined by T215 so `T064` covers copy/move propagation, `SROA`, return-slot construction, and call-graph inlining while `T614` covers specialization, devirtualization, and tail-call optimization.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T064/build` and `python tools/axtest.py --compiler build-snap-T064/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-10-06 02:31:24 covers += REQ-TYP-001, REQ-TYP-002, REQ-TYP-003, REQ-TYP-004, REQ-TYP-005, REQ-TYP-006 (metadata only)
- 2026-11-03 02:41:00 refined scope, covers, and dependencies in T215 (P15 phase planning)
- 2026-11-06 23:15:00 added T610 to depends (ADR-0037: serialize compiler/opt path overlap with T610)
