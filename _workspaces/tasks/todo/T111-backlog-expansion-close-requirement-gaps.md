---
id: T111
title: Backlog expansion — close every requirement gap, add covers to all tasks
phase: P0-traceability
owner: axiom-architect
reviewer: axiom-qa
depends: [T110]
priority: 9
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/COVERAGE.md, spec/SPEC-00-bootstrap.md, spec/ROADMAP.md]
spec: [spec/requirements/CATALOG.md, spec/COVERAGE.md, spec/ROADMAP.md]
---
# T111 — Backlog expansion

## Goal
Turn the coverage matrix into a complete plan: every requirement of the normative corpus is planned
by a task, merged, deferred (post-v1 only) or rejected by ADR; every task declares `covers:`.

## Scope
- Phase C of the extraction procedure.
- Follow `spec/ROADMAP.md` (binding frame). v1-core gaps → new/extended tasks in P0–P10 (one-sitting sized, correct deps/owners, acceptance as tests). Requirements belonging to P11–P23 → status `EPIC(E<phase>.<n>)` of the matching roadmap epic (the phase planning task T2NN turns them into tasks later). post-v1 ecosystem → `EPIC(E24.x)` or `DEFERRED(<reason>)`.
- A requirement that fits no existing epic → ADR + new epic in ROADMAP §3 (with change-log entry); never an ad-hoc task.
- Extend scope of existing todo tasks only where they stay one-sitting sized; never rewrite tasks already in doing/ or done/ — add follow-up tasks instead.
- Update SPEC-00 milestone ladder if P0–P10 phases change.

## Acceptance
- [ ] `taskctl.py validate` OK.
- [ ] `reqcov.py --strict` exits 0 (zero GAP, zero problems).
- [ ] COVERAGE.md updated with final counts (tasks per phase, requirements per tier).
- [ ] Report `_workspaces/reports/T111-report.md` listing new tasks (id, title, phase, covers count) under `## Files changed`.

## Out of scope
- Implementing anything.

## Notes
- Critical board-level task (priority < 10): runs alone, so no agent moves task files while you edit.
- Only discussions/ is non-normative; everything else in docs/base counts.
