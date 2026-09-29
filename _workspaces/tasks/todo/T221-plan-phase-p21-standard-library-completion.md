---
id: T221
title: Plan phase P21 — Standard library completion (expand roadmap epics into tasks)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
depends: [T311, T313]
priority: 6
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/ROADMAP.md]
spec: [spec/ROADMAP.md, spec/requirements/CATALOG.md]
---
# T221 — Plan phase P21: Standard library completion

## Goal
Expand the epics of phase P21 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P21 epics), catalogue rows with `EPIC(E21.*)`, the epics' sources, and the gate reports of the phases this one depends on.
- Create 3–10 tasks per epic with ids in `T900`–`T949`, titles `E21.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T321 depend on every new task; convert catalogue `EPIC(E21.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.

## Acceptance
- [ ] `taskctl.py validate` OK and `reqcov.py --strict` exits 0.
- [ ] Every P21 epic has tasks; gate T321 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T221-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.

