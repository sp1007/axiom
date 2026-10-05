---
id: T111
title: Backlog expansion — close every requirement gap, add covers to all tasks
phase: P0-traceability
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T110]
priority: 9
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/COVERAGE.md, spec/SPEC-00-bootstrap.md, spec/ROADMAP.md, _workspaces/tasks/done/]
spec: [spec/requirements/CATALOG.md, spec/COVERAGE.md, spec/ROADMAP.md]
started: 2026-10-06 02:16:10
unblocks: 1
---
# T111 — Backlog expansion

## Goal
Turn the coverage matrix into a complete plan: every requirement of the normative corpus is planned
by a task, merged, deferred (post-v1 only) or rejected by ADR; every task declares `covers:`.

## Scope
- Phase C of the extraction procedure.
- Follow `spec/ROADMAP.md` (binding frame). v1-core gaps → new/extended tasks in P0–P10 (one-sitting sized, correct deps/owners, acceptance as tests). Requirements belonging to P11–P23 → status `EPIC(E<phase>.<n>)` of the matching roadmap epic (the phase planning task T2NN turns them into tasks later). post-v1 ecosystem → `EPIC(E24.x)` or `DEFERRED(<reason>)`.
- A requirement that fits no existing epic → ADR + new epic in ROADMAP §3 (with change-log entry); never an ad-hoc task.
- Extend scope of existing todo tasks only where they stay one-sitting sized; never rewrite tasks already in doing/ or done/ — add follow-up tasks instead; `covers:` on such tasks is added with `taskctl.py covers <ID> <REQ…>` (metadata only, ADR-0005 §6).
- Update SPEC-00 milestone ladder if P0–P10 phases change.
- Timing rule: a `v1-core` requirement maps only to tasks of P0–P10; follow-up task ids for P0–P10 come from `taskctl.py new-id --phase <P>` (T112–T199).

## Acceptance
- [ ] `taskctl.py validate` OK.
- [ ] `reqcov.py --strict` exits 0 (zero GAP, zero problems).
- [ ] `harness_check.py` exits 0.
- [ ] COVERAGE.md updated with final counts (tasks per phase, requirements per tier).
- [ ] Report `_workspaces/reports/T111-report.md` listing new tasks (id, title, phase, covers count) under `## Files changed`.
- [ ] Every new task file passes `taskctl.py lint`.

## Out of scope
- Implementing anything.

## Notes
- Gate of P0 traceability: T017 (first semantic task) depends on this task; P1/P2 run in parallel with extraction (ADR-0005 §6).
- Critical board-level task (priority < 10): runs alone, so no agent moves task files while you edit.
- Only discussions/ is non-normative; everything else in docs/base counts.

## Log
- 2026-10-06 02:16:10 started (attempt 1) T111-impl
- 2026-10-06 02:48:12 block: needs _workspaces/tasks/done/ in paths to add covers to old tasks
- 2026-10-06 02:48:47 unblocked (cycle 1) 
