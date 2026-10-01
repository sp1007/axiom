---
id: T217
title: Plan phase P17 — Debugging & runtime introspection (expand roadmap epics into tasks)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T316]
priority: 6
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/ROADMAP.md]
spec: [spec/ROADMAP.md, spec/requirements/CATALOG.md]
---
# T217 — Plan phase P17: Debugging & runtime introspection

## Goal
Expand the epics of phase P17 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P17 epics), catalogue rows with `EPIC(E17.*)`, the epics' sources, and the gate reports of the phases this one depends on.
- Create 3–10 tasks per epic with ids in `T700`–`T749`, titles `E17.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T317 depend on every new task; convert catalogue `EPIC(E17.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.
- Add `depends` on the gate task of every phase ROADMAP lists as a prerequisite of an epic (for example E15.5 tasks depend on T312); take ids with `taskctl.py new-id --phase <P>`.

## Acceptance
- [ ] Every new task file passes `taskctl.py lint`; `taskctl.py validate` OK, `reqcov.py --strict` exits 0 and `harness_check.py` exits 0.
- [ ] Every P17 epic has tasks; gate T317 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T217-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.

