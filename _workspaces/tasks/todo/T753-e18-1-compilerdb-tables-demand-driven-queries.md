---
id: T753
title: E18.1 — CompilerDB tables, demand-driven query execution & memoization
phase: P18-compiler-architecture-2-0
owner: axiom-frontend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T752]
priority: 703
status: todo
attempts: 0
paths: [compiler/query/db, tests/run/query_db]
spec: [spec/SPEC-21-query-engine-semantic-db.md, 0153, 0171, tasks/0384, tasks/0530, tasks/0532, tasks/0533, tasks/0781]
covers: [REQ-DRV-001, REQ-DRV-002, REQ-DRV-003, REQ-DRV-004, REQ-DRV-005, REQ-DRV-006, REQ-DRV-007, REQ-DRV-008, REQ-DRV-009, REQ-DRV-010, REQ-DRV-011, REQ-DRV-012, REQ-DRV-013, REQ-TOOL-025, REQ-TOOL-026, REQ-TOOL-027, REQ-TOOL-028, REQ-TOOL-029, REQ-TOOL-030, REQ-TOOL-031, REQ-TOOL-032, REQ-TOOL-033, REQ-TOOL-034, REQ-TOOL-035, REQ-TOOL-036, REQ-TOOL-037, REQ-TOOL-038, REQ-TOOL-039, REQ-TOOL-040, REQ-TOOL-041, REQ-TOOL-042, REQ-TOOL-043, REQ-TOOL-044, REQ-TOOL-045, REQ-TOOL-046, REQ-TOOL-047, REQ-TOOL-048, REQ-TOOL-049, REQ-TOOL-050, REQ-TOOL-051, REQ-TOOL-052, REQ-TOOL-053, REQ-TOOL-054, REQ-TOOL-055, REQ-TOOL-056, REQ-TOOL-057, REQ-TOOL-058, REQ-TOOL-059, REQ-TOOL-060, REQ-TOOL-138, REQ-TOOL-139, REQ-TOOL-140, REQ-TOOL-141, REQ-TOOL-142, REQ-TOOL-143, REQ-TOOL-144, REQ-TOOL-145, REQ-TOOL-146, REQ-TOOL-147, REQ-TOOL-148, REQ-TOOL-149, REQ-TOOL-150, REQ-TOOL-151, REQ-TOOL-152, REQ-TOOL-153, REQ-TOOL-154, REQ-TOOL-155, REQ-TOOL-156, REQ-TOOL-157, REQ-TOOL-158, REQ-TOOL-159, REQ-TOOL-160, REQ-TOOL-161, REQ-TOOL-162, REQ-TOOL-163, REQ-TOOL-164, REQ-TOOL-165, REQ-TOOL-166, REQ-TOOL-167, REQ-TOOL-168, REQ-TOOL-169, REQ-TOOL-170, REQ-TOOL-171, REQ-TOOL-172, REQ-TOOL-173, REQ-TOOL-174, REQ-TOOL-175, REQ-TOOL-176, REQ-TOOL-177, REQ-TOOL-178, REQ-DRV-014, REQ-DRV-015, REQ-DRV-016, REQ-DRV-017, REQ-DRV-019, REQ-TOOL-255, REQ-TOOL-256, REQ-TOOL-257, REQ-TOOL-258, REQ-TOOL-259, REQ-TOOL-260, REQ-TOOL-261, REQ-TOOL-262, REQ-TOOL-263, REQ-TOOL-264, REQ-TOOL-265, REQ-TOOL-266, REQ-TOOL-267, REQ-TOOL-268, REQ-TOOL-269, REQ-TOOL-270, REQ-TOOL-271, REQ-TOOL-272, REQ-TOOL-273, REQ-TOOL-274, REQ-TOOL-275, REQ-TOOL-276, REQ-TOOL-277, REQ-TOOL-278, REQ-TOOL-279, REQ-TOOL-280, REQ-TOOL-281, REQ-TOOL-282, REQ-TOOL-283, REQ-TOOL-284, REQ-TOOL-285, REQ-TOOL-286, REQ-TOOL-287, REQ-TOOL-288, REQ-TOOL-289, REQ-TOOL-290, REQ-TOOL-291, REQ-TOOL-292, REQ-TOOL-293, REQ-TOOL-294, REQ-TOOL-295, REQ-TOOL-296]
---
# T753 — E18.1 — CompilerDB tables, demand-driven query execution & memoization

## Goal
Implement the `CompilerDB` semantic database, typed query keys, demand-driven query evaluation, memoization tables, and dependency DAG recording in `compiler/query/db` per `spec/SPEC-21-query-engine-semantic-db.md`.

## Scope
- Implement `CompilerDB` storage tables in `compiler/query/db` separating immutable input snapshots (`SourceFileId`, `ModuleId`, `TargetConfig`) from derived query tables (`parse_module`, `resolve_module`, `item_signature`, `typeck_body`, `mir_body`).
- Implement demand-driven query invocation with active query stack tracking, automatic caller→callee dependency edge recording, and revision-stamped memoized results.
- Enforce pure, side-effect-free query execution without global mutable state (`0153 §3`, `tasks/0533`).
- Add `inspect --emit=query-graph` to dump the executed query DAG and memoization hit/miss counters deterministically.

## Acceptance
- [ ] Run and dump tests in `tests/run/query_db` verify on-demand evaluation (unreferenced function bodies are not queried during signature-only checks), memoization reuse, and deterministic `--emit=query-graph` output.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T753-report.md` with exact `## Files changed`.

## Out of scope
- Cycle recovery and incremental invalidation (`T754`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T753/build` and `python tools/axtest.py --compiler build-snap-T753/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:56:00 created by T218 (P18 phase planning)
