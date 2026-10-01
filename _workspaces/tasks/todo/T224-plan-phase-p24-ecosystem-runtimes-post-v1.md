---
id: T224
title: Plan phase P24 — Ecosystem runtimes (post-v1) (expand roadmap epics into tasks)
phase: P24-ecosystem-runtimes-post-v1
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T323]
priority: 6
status: deferred
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/ROADMAP.md]
spec: [spec/ROADMAP.md, spec/requirements/CATALOG.md]
---
# T224 — Plan phase P24: Ecosystem runtimes (post-v1)

## Goal
Expand the epics of phase P24 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P24 epics), catalogue rows with `EPIC(E24.*)`, the epics' sources, and the gate reports of the phases this one depends on.
- Create 3–10 tasks per epic with ids in `T1050`–`T1099`, titles `E24.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T324 depend on every new task; convert catalogue `EPIC(E24.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.
- Add `depends` on the gate task of every phase ROADMAP lists as a prerequisite of an epic (for example E15.5 tasks depend on T312); take ids with `taskctl.py new-id --phase <P>`.

## Acceptance
- [ ] Every new task file passes `taskctl.py lint`; `taskctl.py validate` OK, `reqcov.py --strict` exits 0 and `harness_check.py` exits 0.
- [ ] Every P24 epic has tasks; gate T324 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T224-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.
- DEFERRED: post-v1 ecosystem. Starts only when the project owner explicitly schedules it (`taskctl.py unblock T224`). The autopilot must not unblock it.
