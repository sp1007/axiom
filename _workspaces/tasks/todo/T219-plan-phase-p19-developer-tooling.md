---
id: T219
title: Plan phase P19 — Developer tooling (expand roadmap epics into tasks)
phase: P19-developer-tooling
owner: axiom-architect
reviewer: axiom-qa
depends: [T318]
priority: 6
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/ROADMAP.md]
spec: [spec/ROADMAP.md, spec/requirements/CATALOG.md]
---
# T219 — Plan phase P19: Developer tooling

## Goal
Expand the epics of phase P19 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P19 epics), catalogue rows with `EPIC(E19.*)`, the epics' sources, and the gate reports of the phases this one depends on.
- Create 3–10 tasks per epic with ids in `T800`–`T849`, titles `E19.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T319 depend on every new task; convert catalogue `EPIC(E19.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.

## Acceptance
- [ ] `taskctl.py validate` OK and `reqcov.py --strict` exits 0.
- [ ] Every P19 epic has tasks; gate T319 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T219-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.

