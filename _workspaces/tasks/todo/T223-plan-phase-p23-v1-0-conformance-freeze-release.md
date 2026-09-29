---
id: T223
title: Plan phase P23 — v1.0 conformance, freeze & release (expand roadmap epics into tasks)
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-architect
reviewer: axiom-qa
depends: [T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322]
priority: 6
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/ROADMAP.md]
spec: [spec/ROADMAP.md, spec/requirements/CATALOG.md]
---
# T223 — Plan phase P23: v1.0 conformance, freeze & release

## Goal
Expand the epics of phase P23 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P23 epics), catalogue rows with `EPIC(E23.*)`, the epics' sources, and the gate reports of the phases this one depends on.
- Create 3–10 tasks per epic with ids in `T1000`–`T1049`, titles `E23.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T323 depend on every new task; convert catalogue `EPIC(E23.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.

## Acceptance
- [ ] `taskctl.py validate` OK and `reqcov.py --strict` exits 0.
- [ ] Every P23 epic has tasks; gate T323 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T223-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.

